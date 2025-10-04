import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2 } from 'lucide-react';

export default function VoiceDemo() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [stage, setStage] = useState('idle'); // idle, listening, processing, complete

  const sampleResponses = [
    {
      trigger: ['weather', 'temperature', 'forecast'],
      response: "Based on current weather data, it's 72°F and partly cloudy in your area. Tomorrow will be sunny with a high of 78°F."
    },
    {
      trigger: ['time', 'clock', 'hour'],
      response: "The current time is 2:45 PM."
    },
    {
      trigger: ['hello', 'hi', 'hey'],
      response: "Hello! How can I assist you today?"
    },
    {
      trigger: ['help', 'assist', 'support'],
      response: "I'm here to help! You can ask me about the weather, time, reminders, or general questions."
    },
    {
      trigger: ['reminder', 'remember', 'note'],
      response: "I've set a reminder for you. I'll notify you at the specified time."
    }
  ];

  const simulateVoiceInput = () => {
    const sampleInputs = [
      "What's the weather like today?",
      "What time is it?",
      "Hello, how are you?",
      "Can you help me with something?",
      "Set a reminder for tomorrow"
    ];
    
    return sampleInputs[Math.floor(Math.random() * sampleInputs.length)];
  };

  const getRelevantResponse = (input) => {
    const lowerInput = input.toLowerCase();
    
    for (let item of sampleResponses) {
      if (item.trigger.some(keyword => lowerInput.includes(keyword))) {
        return item.response;
      }
    }
    
    return "I understand your request. Let me help you with that.";
  };

  const startListening = () => {
    setIsListening(true);
    setStage('listening');
    setTranscript('');
    setResponse('');

    // Simulate listening for 3 seconds
    setTimeout(() => {
      const userInput = simulateVoiceInput();
      setTranscript(userInput);
      setStage('processing');
      setIsListening(false);

      // Simulate processing for 1.5 seconds
      setTimeout(() => {
        const aiResponse = getRelevantResponse(userInput);
        setResponse(aiResponse);
        setStage('complete');
      }, 1500);
    }, 3000);
  };

  const reset = () => {
    setStage('idle');
    setTranscript('');
    setResponse('');
    setIsListening(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 text-center">
          Voice Assistant Demo
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Click the button to start a voice interaction
        </p>

        {/* Microphone Button */}
        <div className="flex justify-center mb-8">
          <button
            onClick={stage === 'idle' ? startListening : reset}
            disabled={isListening || stage === 'processing'}
            className={`relative rounded-full p-8 transition-all duration-300 transform hover:scale-105 ${
              isListening
                ? 'bg-red-500 animate-pulse'
                : stage === 'processing'
                ? 'bg-yellow-500'
                : stage === 'complete'
                ? 'bg-green-500'
                : 'bg-indigo-600 hover:bg-indigo-700'
            } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg`}
          >
            {isListening ? (
              <Mic className="w-12 h-12 text-white" />
            ) : stage === 'complete' ? (
              <Volume2 className="w-12 h-12 text-white" />
            ) : (
              <MicOff className="w-12 h-12 text-white" />
            )}
          </button>
        </div>

        {/* Status Indicator */}
        <div className="text-center mb-6">
          <div className={`inline-block px-6 py-2 rounded-full text-sm font-semibold ${
            stage === 'listening'
              ? 'bg-red-100 text-red-700'
              : stage === 'processing'
              ? 'bg-yellow-100 text-yellow-700'
              : stage === 'complete'
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-700'
          }`}>
            {stage === 'idle' && 'Ready to listen'}
            {stage === 'listening' && 'Listening...'}
            {stage === 'processing' && 'Processing...'}
            {stage === 'complete' && 'Response ready'}
          </div>
        </div>

        {/* Transcript Display */}
        {transcript && (
          <div className="mb-6 animate-fadeIn">
            <h3 className="text-sm font-semibold text-gray-600 mb-2 flex items-center">
              <Mic className="w-4 h-4 mr-2" />
              You said:
            </h3>
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
              <p className="text-gray-800">{transcript}</p>
            </div>
          </div>
        )}

        {/* Response Display */}
        {response && (
          <div className="animate-fadeIn">
            <h3 className="text-sm font-semibold text-gray-600 mb-2 flex items-center">
              <Volume2 className="w-4 h-4 mr-2" />
              Assistant response:
            </h3>
            <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded">
              <p className="text-gray-800">{response}</p>
            </div>
          </div>
        )}

        {/* Instructions */}
        {stage === 'idle' && (
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>This demo simulates a voice interaction:</p>
            <p className="mt-2">1. Click to start listening (3 seconds)</p>
            <p>2. System processes your input (1.5 seconds)</p>
            <p>3. Receive a relevant response</p>
          </div>
        )}

        {stage === 'complete' && (
          <div className="mt-6 text-center">
            <button
              onClick={reset}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}