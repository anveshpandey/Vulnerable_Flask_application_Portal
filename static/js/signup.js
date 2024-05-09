document.addEventListener('DOMContentLoaded', function() {
    var errorMessage = document.getElementById('error-message');
  
    // Event listener for form submission
    var signupForm = document.getElementById('signup-form');
    signupForm.addEventListener('submit', function(event) {
      event.preventDefault();
  
      // Perform form validation or submit the form data to the server
      var username = document.getElementById('username').value;
      var email = document.getElementById('email').value;
  
      // Example: Check if username or email already exists
      if (username === 'existing_username') {
        showError('Username already exists');
        return;
      }
      if (email === 'existing_email@example.com') {
        showError('Email already exists');
        return;
      }
  
      // If no errors, submit the form
      signupForm.submit();
    });
  
    // Function to display error message
    function showError(message) {
      errorMessage.textContent = message;
      errorMessage.style.display = 'block';
    }
  });
  