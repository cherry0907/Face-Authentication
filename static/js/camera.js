// Camera and face capture functionality

class CameraCapture {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.stream = null;
        this.isCapturing = false;
        
        this.init();
    }
    
    init() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        
        if (this.canvas) {
            this.context = this.canvas.getContext('2d');
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const startCameraBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureBtn');
        const retakeBtn = document.getElementById('retakeBtn');
        
        if (startCameraBtn) {
            startCameraBtn.addEventListener('click', () => this.startCamera());
        }
        
        if (captureBtn) {
            captureBtn.addEventListener('click', () => this.captureImage());
        }
        
        if (retakeBtn) {
            retakeBtn.addEventListener('click', () => this.retakePhoto());
        }
    }
    
    async startCamera() {
        try {
            // Request camera permissions
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.play();
                
                // Update UI
                this.updateCameraUI('streaming');
                
                // Show capture button after video starts playing
                this.video.addEventListener('loadedmetadata', () => {
                    document.getElementById('captureBtn').style.display = 'inline-block';
                    document.getElementById('startCameraBtn').style.display = 'none';
                });
            }
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.handleCameraError(error);
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                track.stop();
            });
            this.stream = null;
        }
        
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    captureImage() {
        if (!this.video || !this.canvas || !this.context) {
            showToast('error', 'Camera not initialized properly');
            return;
        }
        
        try {
            // Set canvas dimensions to match video
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            
            // Draw current video frame to canvas
            this.context.drawImage(this.video, 0, 0);
            
            // Convert canvas to base64 image
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Store the image data
            const faceImageInput = document.getElementById('faceImageData');
            if (faceImageInput) {
                faceImageInput.value = imageData;
            }
            
            // Show preview
            this.showPreview(imageData);
            
            // Stop camera
            this.stopCamera();
            
            // Update UI
            this.updateCameraUI('captured');
            
            // Dispatch custom event for form validation
            document.dispatchEvent(new CustomEvent('faceCaptured', {
                detail: { imageData: imageData }
            }));
            
            showToast('success', 'Face captured successfully!');
            
        } catch (error) {
            console.error('Error capturing image:', error);
            showToast('error', 'Failed to capture image. Please try again.');
        }
    }
    
    showPreview(imageData) {
        const preview = document.getElementById('facePreview');
        const capturedDiv = document.getElementById('capturedImage');
        
        if (preview && capturedDiv) {
            preview.src = imageData;
            capturedDiv.style.display = 'block';
            
            if (this.video) {
                this.video.style.display = 'none';
            }
        }
    }
    
    retakePhoto() {
        // Clear stored image data
        const faceImageInput = document.getElementById('faceImageData');
        if (faceImageInput) {
            faceImageInput.value = '';
        }
        
        // Hide preview
        const capturedDiv = document.getElementById('capturedImage');
        if (capturedDiv) {
            capturedDiv.style.display = 'none';
        }
        
        // Show video again
        if (this.video) {
            this.video.style.display = 'block';
        }
        
        // Update UI
        this.updateCameraUI('initial');
        
        // Restart camera
        this.startCamera();
    }
    
    updateCameraUI(state) {
        const startBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureBtn');
        const retakeBtn = document.getElementById('retakeBtn');
        
        switch (state) {
            case 'initial':
                if (startBtn) startBtn.style.display = 'inline-block';
                if (captureBtn) captureBtn.style.display = 'none';
                if (retakeBtn) retakeBtn.style.display = 'none';
                break;
                
            case 'streaming':
                if (startBtn) startBtn.style.display = 'none';
                if (captureBtn) captureBtn.style.display = 'inline-block';
                if (retakeBtn) retakeBtn.style.display = 'none';
                break;
                
            case 'captured':
                if (startBtn) startBtn.style.display = 'none';
                if (captureBtn) captureBtn.style.display = 'none';
                if (retakeBtn) retakeBtn.style.display = 'inline-block';
                break;
        }
    }
    
    handleCameraError(error) {
        let message = 'Unable to access camera. ';
        
        switch (error.name) {
            case 'NotAllowedError':
                message += 'Please allow camera access and refresh the page.';
                break;
            case 'NotFoundError':
                message += 'No camera found on this device.';
                break;
            case 'NotSupportedError':
                message += 'Camera not supported in this browser.';
                break;
            case 'NotReadableError':
                message += 'Camera is being used by another application.';
                break;
            default:
                message += 'Please check your camera and try again.';
        }
        
        showToast('error', message);
    }
    
    // Check if camera is supported
    static isCameraSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }
    
    // Cleanup method
    destroy() {
        this.stopCamera();
    }
}

// Initialize camera when DOM is loaded
let cameraCapture = null;

document.addEventListener('DOMContentLoaded', function() {
    // Check camera support
    if (!CameraCapture.isCameraSupported()) {
        showToast('error', 'Camera not supported in this browser. Please use a modern browser.');
        return;
    }
    
    // Initialize camera capture if video element exists
    const videoElement = document.getElementById('video');
    if (videoElement) {
        cameraCapture = new CameraCapture();
    }
});

// Cleanup when page unloads
window.addEventListener('beforeunload', function() {
    if (cameraCapture) {
        cameraCapture.destroy();
    }
});

// Export for use in other scripts
window.CameraCapture = CameraCapture;