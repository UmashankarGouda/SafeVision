// Touch-friendly recording controls for mobile
const recordBtn = document.getElementById('record-btn');
let recording = false;

function startRecording() {
    fetch('/api/recording/start', {method: 'POST'}).then(() => {
        recording = true;
        recordBtn.innerText = 'Stop Recording';
    });
}

function stopRecording() {
    fetch('/api/recording/stop', {method: 'POST'}).then(() => {
        recording = false;
        recordBtn.innerText = 'Start Recording';
    });
}

recordBtn.addEventListener('click', () => {
    if (recording) stopRecording();
    else startRecording();
});

// Gesture support for mobile (swipe up to start, down to stop)
let touchStartY = null;
document.addEventListener('touchstart', e => {
    touchStartY = e.touches[0].clientY;
});
document.addEventListener('touchend', e => {
    if (touchStartY === null) return;
    let touchEndY = e.changedTouches[0].clientY;
    if (touchEndY < touchStartY - 50) startRecording();
    if (touchEndY > touchStartY + 50) stopRecording();
    touchStartY = null;
});
