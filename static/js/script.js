function validateFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file');
        return false;
    }
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov'];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        alert('Invalid file type. Allowed: jpg, jpeg, png, mp4, avi, mov');
        return false;
    }
    return true;
}
