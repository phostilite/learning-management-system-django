// static/js/enrollment.js
document.addEventListener('DOMContentLoaded', function() {
    const enrollmentButtons = document.querySelectorAll('.enroll-button');
    const modal = document.getElementById('enrollment-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalSubtitle = document.getElementById('modal-subtitle');
    const modalInstructor = document.getElementById('modal-instructor');
    const modalDuration = document.getElementById('modal-duration');
    const modalLevel = document.getElementById('modal-level');
    const modalLanguage = document.getElementById('modal-language');
    const modalDescription = document.getElementById('modal-description');
    const modalImage = document.getElementById('modal-image');
    const enrollButton = document.getElementById('enroll-button');

    enrollmentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const enrollmentType = this.dataset.enrollmentType;
            const objectId = this.dataset.objectId;
            const title = this.dataset.title;
            const subtitle = this.dataset.subtitle;
            const instructor = this.dataset.instructor;
            const duration = this.dataset.duration;
            const level = this.dataset.level;
            const language = this.dataset.language;
            const description = this.dataset.description;
            const imageUrl = this.dataset.imageUrl;

            modalTitle.textContent = enrollmentType === 'course' ? 'Course Enrollment' : 'Program Enrollment';
            modalSubtitle.textContent = title;
            modalInstructor.textContent = instructor;
            modalDuration.textContent = duration;
            modalLevel.textContent = level;
            modalLanguage.textContent = language;
            modalDescription.textContent = description;
            modalImage.src = imageUrl;

            enrollButton.onclick = function() {
                enrollUser(enrollmentType, objectId);
            };

            modal.classList.remove('hidden');
        });
    });

    function enrollUser(enrollmentType, objectId) {
        fetch('/en/user/learner/enroll/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `enrollment_type=${enrollmentType}&object_id=${objectId}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                modal.classList.add('hidden');
                window.location.href = '/en/user/learner/enrollments/';
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});