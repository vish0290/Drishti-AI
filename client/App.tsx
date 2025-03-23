import {
  CameraMode,
  CameraType,
  CameraView,
  useCameraPermissions,
} from "expo-camera";
import { useRef, useState, useEffect } from "react";
import { Button, Pressable, StyleSheet, Text, View, TextInput, ActivityIndicator, Alert } from "react-native";
import { Image } from "expo-image";
import { FontAwesome6 } from "@expo/vector-icons";
import { Ionicons } from "@expo/vector-icons";
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [audioPermission, setAudioPermission] = useState(false);
  const ref = useRef<CameraView>(null);
  const [uri, setUri] = useState<string | null>(null);
  const [facing, setFacing] = useState<CameraType>("back");
  const [mlUrl, setMlUrl] = useState<string>("");
  const [showUrlInput, setShowUrlInput] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [userQuery, setUserQuery] = useState<string>("what is happening here");
  const [transcriptionStatus, setTranscriptionStatus] = useState<string | null>(null);
  const [pendingImageUri, setPendingImageUri] = useState<string | null>(null);

  // Request audio permissions and load saved ML URL
  useEffect(() => {
    const requestAudioPermission = async () => {
      const { status } = await Audio.requestPermissionsAsync();
      setAudioPermission(status === "granted");
    };
    
    const loadSavedUrl = async () => {
      try {
        const savedUrl = await AsyncStorage.getItem('mlUrl');
        if (savedUrl) {
          setMlUrl(savedUrl);
          setShowUrlInput(false);
        }
      } catch (error) {
        console.error("Failed to load saved URL:", error);
      }
    };
    
    requestAudioPermission();
    loadSavedUrl();
    
    // Clean up audio when component unmounts
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
      if (recording) {
        recording.stopAndUnloadAsync();
      }
    };
  }, [sound, recording]); // Added sound and recording as dependencies

  // Start recording audio
  const startRecording = async () => {
    try {
      if (!audioPermission) {
        Alert.alert("Permission Required", "Audio recording permission is required");
        return;
      }
      
      // Take picture first
      const photo = await ref.current?.takePictureAsync();
      if (!photo?.uri) {
        throw new Error("Failed to capture image");
      }
      
      // Store the image URI for later processing
      setPendingImageUri(photo.uri);
      
      console.log('Picture taken, starting recording...');
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(newRecording);
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start capture process', error);
      Alert.alert("Error", "Failed to capture image or start recording");
      setPendingImageUri(null);
    }
  };

  // Stop recording and transcribe audio
  const stopRecording = async () => {
    console.log('Stopping recording...');
    if (!recording) return;
    
    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });
      
      const audioUri = recording.getURI();
      setRecording(null);
      
      if (audioUri && pendingImageUri) {
        await transcribeAudio(audioUri, pendingImageUri);
      } else {
        throw new Error("Missing audio or image data");
      }
    } catch (error) {
      console.error('Failed to process recording', error);
      Alert.alert("Error", "Failed to process recording");
      setRecording(null);
      setIsRecording(false);
      setPendingImageUri(null);
    }
  };

  // Convert audio to text
  const transcribeAudio = async (audioUri: string, imageUri: string) => {
    try {
      setTranscriptionStatus("Recording processed...");
      
      const fileInfo = await FileSystem.getInfoAsync(audioUri);
      if (!fileInfo.exists) {
        throw new Error("Audio file doesn't exist");
      }
      
      console.log("Audio file exists at:", audioUri);
      console.log("File size:", fileInfo.size);
      
      setTranscriptionStatus("Converting audio...");
      
      // Read the audio file as base64
      const base64Audio = await FileSystem.readAsStringAsync(audioUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      
      console.log("Successfully converted audio to base64, length:", base64Audio.length);
      console.log("Sending to endpoint:", `${mlUrl}/transcribe`);
      
      setTranscriptionStatus("Transcribing speech...");
      
      // Send to a transcription service
      const response = await fetch(`${mlUrl}/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio: base64Audio,
          format: "wav",
        }),
        timeout: 10000,
      });
      
      console.log("Transcription response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => "Unable to get error details");
        console.error("Transcription error response:", errorText);
        throw new Error(`Transcription request failed with status ${response.status}`);
      }
      
      setTranscriptionStatus("Understanding content...");
      
      const data = await response.json();
      console.log("Transcription response data:", data);
      
      if (!data.text) {
        console.warn("No text field in response:", data);
      }
      
      const transcribedText = data.text || "what is happening here";
      console.log("Using transcribed text:", transcribedText);
      setUserQuery(transcribedText);
      
      setTranscriptionStatus("Processing image...");
      
      // Now process the image that was already captured
      setUri(imageUri);
      processImage(imageUri);
      
    } catch (error) {
      console.error("Error transcribing audio:", error);
      
      // More detailed error reporting
      if (error instanceof TypeError && error.message.includes('Network request failed')) {
        Alert.alert(
          "Network Error", 
          "Could not connect to the transcription service. Please check your internet connection and the API URL."
        );
      } else {
        Alert.alert(
          "Transcription Failed", 
          "Using default query instead. Error: " + (error instanceof Error ? error.message : String(error))
        );
      }
      
      setUserQuery("what is happening here");
      setTranscriptionStatus("Processing image...");
      
      // Still process the image with default query
      if (imageUri) {
        setUri(imageUri);
        processImage(imageUri);
      }
    } finally {
      setPendingImageUri(null);
      setTranscriptionStatus(null);
    }
  };

  // Handle URL saving
  const saveUrl = async () => {
    if (!mlUrl.trim()) {
      Alert.alert("Error", "Please enter a valid URL");
      return;
    }
    
    try {
      await AsyncStorage.setItem('mlUrl', mlUrl);
      setShowUrlInput(false);
    } catch (error) {
      console.error("Failed to save URL:", error);
      Alert.alert("Error", "Failed to save URL");
    }
  };

  // Convert image to base64
  const imageToBase64 = async (imageUri: string) => {
    try {
      const base64 = await FileSystem.readAsStringAsync(imageUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      return base64;
    } catch (error) {
      console.error("Error converting image to base64:", error);
      throw error;
    }
  };

  // Process image with ML API
  const processImage = async (imageUri: string) => {
    try {
      setIsProcessing(true);
      const base64Image = await imageToBase64(imageUri);
      
      const response = await fetch(`${mlUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          img_base64: base64Image,
          user_input: userQuery
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      // Get audio file from response
      const audioBlob = await response.blob();
      const fileUri = FileSystem.documentDirectory + 'response.wav';
      
      // Write to file system
      const base64Data = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (typeof reader.result === 'string') {
            resolve(reader.result.split(',')[1]);
          }
        };
        reader.readAsDataURL(audioBlob);
      });
      
      await FileSystem.writeAsStringAsync(fileUri, base64Data, {
        encoding: FileSystem.EncodingType.Base64,
      });
      
      // Play audio
      await playSound(fileUri);
      
    } catch (error) {
      console.error("Error processing image:", error);
      Alert.alert("Error", "Failed to process image");
    } finally {
      setIsProcessing(false);
    }
  };

  // Play audio file
  const playSound = async (audioUri: string) => {
    try {
      if (sound) {
        await sound.unloadAsync();
      }
      
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: audioUri },
        { shouldPlay: true }
      );
      
      setSound(newSound);
      
      // Unload sound when done playing
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          newSound.unloadAsync();
        }
      });
    } catch (error) {
      console.error("Error playing sound:", error);
      Alert.alert("Error", "Failed to play audio response");
    }
  };

  if (!permission) {
    return null;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={{ textAlign: "center" }}>
          We need your permission to use the camera
        </Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  // URL configuration screen
  if (showUrlInput) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Enter ML API URL</Text>
        <TextInput
          style={styles.input}
          value={mlUrl}
          onChangeText={setMlUrl}
          placeholder="https://example.com/api"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <Button title="Save and Continue" onPress={saveUrl} />
      </View>
    );
  }

  const takePicture = async () => {
    if (isProcessing) return;
    
    setTranscriptionStatus(null);
    setPendingImageUri(null);
    
    const photo = await ref.current?.takePictureAsync();
    if (photo?.uri) {
      setUri(photo.uri);
      processImage(photo.uri);
    }
  };

  const toggleFacing = () => {
    setFacing((prev) => (prev === "back" ? "front" : "back"));
  };

  const renderPicture = () => {
    return (
      <View style={styles.imageContainer}>
        <Image
          source={{ uri }}
          contentFit="contain"
          style={styles.capturedImage}
        />
        {isProcessing ? (
          <View style={styles.loaderContainer}>
            <ActivityIndicator size="large" color="#0000ff" style={styles.loader} />
            <Text style={styles.queryText}>Query: "{userQuery}"</Text>
          </View>
        ) : (
          <View>
            <Text style={styles.queryText}>Query: "{userQuery}"</Text>
            <Button onPress={() => setUri(null)} title="Take another picture" />
          </View>
        )}
      </View>
    );
  };

  const renderCamera = () => {
    return (
      <CameraView
        style={styles.camera}
        ref={ref}
        mode="picture"
        facing={facing}
        mute={false}
        mirrored={facing === "front"}
        responsiveOrientationWhenOrientationLocked
      >
        {pendingImageUri && isRecording && (
          <View style={styles.previewOverlay}>
            <Image
              source={{ uri: pendingImageUri }}
              style={styles.previewImage}
              contentFit="cover"
            />
          </View>
        )}
        
        {transcriptionStatus && (
          <View style={styles.transcriptionStatusContainer}>
            <ActivityIndicator size="small" color="#fff" />
            <Text style={styles.transcriptionStatusText}>{transcriptionStatus}</Text>
          </View>
        )}
        
        {isRecording && (
          <View style={styles.recordingIndicator}>
            <Text style={styles.recordingText}>Recording... (Hold to record, release to send)</Text>
          </View>
        )}
        
        <View style={styles.shutterContainer}>
          <Pressable onPress={toggleFacing} style={styles.iconButton}>
            <FontAwesome6 name="rotate-left" size={32} color="white" />
          </Pressable>
          
          <Pressable 
            onPressIn={startRecording}
            onPressOut={stopRecording}
            disabled={isProcessing || transcriptionStatus !== null}
          >
            {({ pressed }) => (
              <View
                style={[
                  styles.shutterBtn,
                  {
                    opacity: (pressed || isProcessing || transcriptionStatus !== null) ? 0.5 : 1,
                    backgroundColor: isRecording ? "rgba(255,0,0,0.3)" : "transparent",
                  },
                ]}
              >
                <View style={styles.shutterBtnInner} />
              </View>
            )}
          </Pressable>
          
          <Pressable 
            onPress={() => setShowUrlInput(true)} 
            style={styles.iconButton}
            disabled={isProcessing || transcriptionStatus !== null}
          >
            <Ionicons name="settings" size={32} color={isProcessing || transcriptionStatus !== null ? "gray" : "white"} />
          </Pressable>
        </View>
      </CameraView>
    );
  };

  return (
    <View style={styles.container}>
      {uri ? renderPicture() : renderCamera()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 20,
  },
  input: {
    width: "100%",
    height: 50,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 5,
    marginBottom: 20,
    padding: 10,
    backgroundColor: "#fff",
  },
  camera: {
    flex: 1,
    width: "100%",
  },
  shutterContainer: {
    position: "absolute",
    bottom: 44,
    left: 0,
    width: "100%",
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 30,
  },
  shutterBtn: {
    borderWidth: 5,
    borderColor: "white",
    width: 85,
    height: 85,
    borderRadius: 45,
    alignItems: "center",
    justifyContent: "center",
  },
  shutterBtnInner: {
    width: 70,
    height: 70,
    borderRadius: 50,
    backgroundColor: "white",
  },
  iconButton: {
    padding: 10,
  },
  imageContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
  },
  capturedImage: {
    width: "100%",
    height: "80%",
    borderRadius: 10,
  },
  loader: {
    marginTop: 20,
  },
  loaderContainer: {
    marginTop: 20,
    alignItems: "center",
  },
  recordingIndicator: {
    position: "absolute",
    top: 50,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255, 0, 0, 0.5)",
    padding: 10,
    alignItems: "center",
  },
  recordingText: {
    color: "white",
    fontWeight: "bold",
  },
  queryText: {
    color: "white",
    fontSize: 16,
    textAlign: "center",
    marginVertical: 10,
  },
  transcriptionStatusContainer: {
    position: "absolute",
    top: 100,
    left: 0,
    right: 0,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    padding: 15,
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
  },
  transcriptionStatusText: {
    color: "white",
    fontWeight: "bold",
    marginLeft: 10,
    fontSize: 16,
  },
  previewOverlay: {
    position: "absolute",
    top: 150,
    right: 20,
    width: 120,
    height: 160,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: "white",
    overflow: "hidden",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
  },
  previewImage: {
    width: "100%",
    height: "100%",
  },
});