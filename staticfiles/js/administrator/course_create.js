const form = document.getElementById('course-form');
const steps = document.querySelectorAll('.form-step');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const submitBtn = document.getElementById('submit-btn');
const progressBar = document.getElementById('progress-bar');
const progressPercentage = document.getElementById('progress-percentage');
const stepIndicators = document.querySelectorAll('.steps li');
const addResourceBtn = document.getElementById('add-resource');
const learningResources = document.getElementById('learning-resources');

let currentStep = 1;
const totalSteps = steps.length;

function updateStep(step) {
    steps.forEach((s, index) => s.classList.toggle('active', index + 1 === step));

    stepIndicators.forEach((indicator, index) => {
        indicator.classList.toggle('text-primary', index + 1 <= step);
        indicator.classList.toggle('text-gray-400', index + 1 > step);
    });

    const progress = ((step - 1) / (totalSteps - 1)) * 100;
    progressBar.style.width = `${progress}%`;
    progressPercentage.textContent = `${Math.round(progress)}%`;

    prevBtn.style.display = step === 1 ? 'none' : 'inline-flex';
    nextBtn.style.display = step === totalSteps ? 'none' : 'inline-flex';
    submitBtn.style.display = step === totalSteps ? 'inline-flex' : 'none';
}

function createResourceHTML(resourceCount) {
    return `
        <div class="learning-resource mb-4 p-4 border border-gray-200 rounded-md">
            <h3 class="text-xl font-semibold mb-3">Resource ${resourceCount}</h3>
            <div class="mb-4">
                <label for="resource-title-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">Resource Title</label>
                <input type="text" id="resource-title-${resourceCount}" name="resource-title-${resourceCount}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div class="mb-4">
                <label for="resource-type-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">Resource Type</label>
                <select id="resource-type-${resourceCount}" name="resource-type-${resourceCount}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary">
                    <option value="video">Video</option>
                    <option value="document">Document</option>
                    <option value="link">External Link</option>
                </select>
            </div>
            <div class="mb-4">
                <label for="resource-description-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea id="resource-description-${resourceCount}" name="resource-description-${resourceCount}" rows="4" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"></textarea>
            </div>
            <div class="mb-4">
                <label for="resource-content-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">Content</label>
                <input type="file" id="resource-content-${resourceCount}" name="resource-content-${resourceCount}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary">
            </div>
            <div class="mb-4">
                <label for="resource-external-url-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">External URL</label>
                <input type="url" id="resource-external-url-${resourceCount}" name="resource-external-url-${resourceCount}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary" placeholder="https://example.com">
            </div>
            <div class="mb-4">
                <label for="resource-order-${resourceCount}" class="block text-sm font-medium text-gray-700 mb-2">Resource Order</label>
                <input type="number" id="resource-order-${resourceCount}" name="resource-order-${resourceCount}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary" placeholder="1">
            </div>
            <button type="button" class="delete-resource bg-red-500 text-white px-3 py-1 rounded-md">Delete</button>
        </div>
    `;
}

function addResource() {
    const resourceCount = learningResources.children.length + 1;
    const newResource = document.createElement('div');
    newResource.innerHTML = createResourceHTML(resourceCount);
    learningResources.appendChild(newResource);
}

function deleteResource(event) {
    if (event.target.classList.contains('delete-resource')) {
        event.target.closest('.learning-resource').remove();
    }
}

nextBtn.addEventListener('click', () => {
    if (currentStep < totalSteps) {
        currentStep++;
        updateStep(currentStep);
    }
});

prevBtn.addEventListener('click', () => {
    if (currentStep > 1) {
        currentStep--;
        updateStep(currentStep);
    }
});

addResourceBtn.addEventListener('click', addResource);

learningResources.addEventListener('click', deleteResource);

form.addEventListener('submit', (e) => {
    e.preventDefault();
    currentStep = totalSteps;
    updateStep(currentStep);
    
    // Simulate form submission
    setTimeout(() => {
        alert('Course created successfully!');
        // Here you would typically send the form data to your server
        console.log('Form submitted!');
    }, 3000); // 3 seconds delay to show the animation
});

// Initialize the form
updateStep(currentStep);