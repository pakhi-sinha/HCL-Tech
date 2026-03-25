const reviewBtn = document.getElementById('review-btn');
const codeInput = document.getElementById('code-input');
const emptyState = document.getElementById('empty-state');
const loader = document.getElementById('loader');
const resultsBox = document.getElementById('results');

reviewBtn.addEventListener('click', async () => {
    const code = codeInput.value.trim();
    if (!code) {
        alert("Please paste some code to review!");
        return;
    }

    // UI Updates
    emptyState.classList.add('hidden');
    resultsBox.classList.add('hidden');
    loader.classList.remove('hidden');
    reviewBtn.disabled = true;
    reviewBtn.innerText = "Analyzing with Gemini...";

    try {
        const response = await fetch("http://localhost:8000/review", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code_snippet: code })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();
        
        // Populate Data
        document.getElementById('confidence-score').innerText = data.confidence_score;
        
        // Circular progress animation logic
        const circle = document.querySelector('.score-circle');
        circle.style.background = `conic-gradient(var(--success) ${data.confidence_score}%, transparent 0)`;
        
        // Color coding score
        if(data.confidence_score < 50) {
            circle.style.color = 'var(--danger)';
            circle.style.background = `conic-gradient(var(--danger) ${data.confidence_score}%, transparent 0)`;
            circle.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.2)';
        }
        else if(data.confidence_score < 80) {
            circle.style.color = 'var(--warning)';
            circle.style.background = `conic-gradient(var(--warning) ${data.confidence_score}%, transparent 0)`;
            circle.style.boxShadow = '0 0 20px rgba(245, 158, 11, 0.2)';
        }
        else {
            circle.style.color = 'var(--success)';
            circle.style.background = `conic-gradient(var(--success) ${data.confidence_score}%, transparent 0)`;
            circle.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.2)';
        }

        const createList = (items, targetId) => {
            const ul = document.getElementById(targetId);
            ul.innerHTML = '';
            if(!items || items.length === 0) {
                ul.innerHTML = '<li>No issues found!</li>';
            } else {
                items.forEach(item => {
                    const li = document.createElement('li');
                    li.innerText = item;
                    ul.appendChild(li);
                });
            }
        };

        createList(data.merged_bugs, 'bugs-list');
        createList(data.security_flaws, 'flaws-list');

        document.getElementById('refactored-code').innerText = data.refactored_code || "No refactoring suggested.";

        // Reveal Results
        loader.classList.add('hidden');
        resultsBox.classList.remove('hidden');

    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while fetching the review from the AI API. Please make sure the backend is running via Uvicorn on port 8000!");
        
        loader.classList.add('hidden');
        emptyState.classList.remove('hidden');
    } finally {
        reviewBtn.disabled = false;
        reviewBtn.innerText = "Run Gemini Review";
    }
});
