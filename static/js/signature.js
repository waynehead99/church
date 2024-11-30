class SignaturePad {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.points = [];
        this.isDrawing = false;
        
        // Set canvas size
        this.resize();

        // Set default styles
        this.ctx.strokeStyle = options.penColor || '#000000';
        this.ctx.lineWidth = options.penWidth || 2;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        // Add event listeners
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('touchstart', this.onTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this.onTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this.onTouchEnd.bind(this));
        
        // Handle window resize
        window.addEventListener('resize', this.resize.bind(this));
    }

    resize() {
        const rect = this.canvas.parentNode.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = 150;
    }

    onMouseDown(event) {
        this.isDrawing = true;
        const point = this.getPoint(event);
        this.points.push(point);
        this.ctx.beginPath();
        this.ctx.moveTo(point.x, point.y);
    }

    onMouseMove(event) {
        if (!this.isDrawing) return;
        const point = this.getPoint(event);
        this.points.push(point);
        this.ctx.lineTo(point.x, point.y);
        this.ctx.stroke();
    }

    onMouseUp() {
        this.isDrawing = false;
    }

    onTouchStart(event) {
        event.preventDefault();
        if (event.touches.length === 1) {
            this.onMouseDown(event.touches[0]);
        }
    }

    onTouchMove(event) {
        event.preventDefault();
        if (event.touches.length === 1) {
            this.onMouseMove(event.touches[0]);
        }
    }

    onTouchEnd(event) {
        event.preventDefault();
        this.onMouseUp();
    }

    getPoint(event) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        };
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.points = [];
    }

    isEmpty() {
        return this.points.length === 0;
    }

    toDataURL() {
        return this.canvas.toDataURL('image/png');
    }
}

// Initialize signature pad when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('liability-signature');
    if (!canvas) return;  // Exit if canvas not found
    
    window.signaturePad = new SignaturePad(canvas, {
        penColor: '#000000'
    });

    // Form submission handler
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        const photoRelease = document.getElementById('photo_release');
        
        if (photoRelease.checked && window.signaturePad.isEmpty()) {
            e.preventDefault();
            alert('Please sign the photo release form');
            return false;
        }
    });
});
