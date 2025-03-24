# Drishti-AI

Drishti-AI is an assistive vision application that helps users understand their surroundings through image analysis. The system captures images, processes them with advanced AI models, and provides audio descriptions back to the user.

## Features

- **Image Analysis**: Processes images to describe content and answer user queries
- **Voice Interaction**: Supports voice commands and audio responses
- **Mobile Client**: React Native mobile app for capturing images and interacting with the system

## System Architecture

The application consists of three main components:

1. **Mobile Client**: React Native app that captures images and records user queries
2. **Backend API**: FastAPI server that processes requests and connects to ML services
3. **AI Models**: Integrates with Google Gemini for image analysis and Kokoro for text-to-speech

## Deployment Options

### Local Deployment (Stand-alone)

The `stand_alone` directory contains a simplified version for local deployment without user authentication.

#### Prerequisites

- Python 3.11+
- Docker (optional)

#### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/vish0290/Drishti-AI.git
   cd Drishti-AI
   ```

2. Set up environment variables:

   ```bash
   cp "Example env.txt" .env
   ```

   Edit `.env` file to add your Google Gemini API key:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. Create necessary directories:

   ```bash
   mkdir -p stand_alone/audio
   ```

4. Install dependencies:

   ```bash
   cd stand_alone
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8282
   ```

#### Docker Deployment (Stand-alone)

```bash
cd stand_alone
docker build -t drishti-ai-standalone .
docker run -p 8282:8282 -v $(pwd)/audio:/app/audio --env-file ../.env drishti-ai-standalone
```

### Cloud Deployment (Backend)

The `backend` directory contains the full version with user authentication for cloud deployment.

#### Prerequisites

- Python 3.11+
- MongoDB database
- Docker (optional)

#### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/Drishti-AI.git
   cd Drishti-AI
   ```

2. Set up environment variables:

   ```bash
   cp "Example env.txt" .env
   ```

   Edit `.env` file to add required configuration:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   DB_URI=your_mongodb_connection_string
   DB_NAME=your_database_name
   USER_COLLECTION=users
   API_KEY_SECRET=your_secret_key
   ```

3. Create necessary directories:

   ```bash
   mkdir -p backend/audio
   ```

4. Install dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8282
   ```

#### Docker Deployment (Backend)

```bash
cd backend
docker build -t drishti-ai-backend .
docker run -p 8282:8282 -v $(pwd)/audio:/app/audio --env-file ../.env drishti-ai-backend
```

## Mobile Client Setup

### Quick Setup (Using Pre-built APK)

1. Download the `drishti_ai.apk` file to your Android device (iOS version coming soon)

2. If running the server locally, set up port forwarding to make it accessible:

   - In VS Code, you can use the port forwarding feature as shown in the `port forwarding.mkv` video
   - This allows your mobile device to connect to the locally running server
   - [![Watch the video]](https://raw.githubusercontent.com/Drishti-AI/branch/path/to/video.mp4)




3. Once installed, open the app and enter the URL:
   - For local deployment with port forwarding: `http://your-forwarded-url:port`
   - For cloud deployment: `https://your-cloud-domain.com`

### Development Setup

1. Navigate to the client directory:

   ```bash
   cd client
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the application:

   ```bash
   npm start
   ```

4. Install the app on your device using Expo Go or build a native app:

   ```bash
   expo build:android
   # or
   expo build:ios
   ```

5. When first launching the app, you'll be prompted to enter the API URL:
    ![Drishti AI App Screen shot for ML URL](https://example.com/screenshot.png)



## Usage

1. Open the Drishti AI app.

2. Press and hold the shutter button to record a query.

3. The system processes the image and audio.

4. The audio response is played back to the user.


## API Endpoints

### Stand-alone Version

- `GET /`: Health check
- `POST /transcribe`: Convert audio to text
- `POST /query`: Process image and user query

### Backend Version

- `GET /`: Health check
- `POST /register`: Register a new user
- `POST /login`: Authenticate a user
- `POST /transcribe`: Convert audio to text (requires API key)
- `POST /query`: Process image and user query (requires API key)



## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
