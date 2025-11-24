document.addEventListener('DOMContentLoaded', function () {
    const markdownField = document.getElementById('id_body_markdown');
    if (!markdownField) return;

    // Create preview container
    const previewContainer = document.createElement('div');
    previewContainer.className = 'markdown-preview-container';

    const previewHeader = document.createElement('h2');
    previewHeader.textContent = 'Live Preview';
    previewContainer.appendChild(previewHeader);

    const previewContent = document.createElement('div');
    previewContent.className = 'markdown-preview-content';
    previewContainer.appendChild(previewContent);

    // Insert after the markdown field
    markdownField.parentNode.insertBefore(previewContainer, markdownField.nextSibling);

    // Function to update preview
    function updatePreview() {
        const markdownText = markdownField.value;
        // Use marked library if available, otherwise fallback or wait
        if (typeof marked !== 'undefined') {
            previewContent.innerHTML = marked.parse(markdownText);

            // Apply syntax highlighting if hljs is available
            if (typeof hljs !== 'undefined') {
                previewContent.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
        } else {
            previewContent.innerHTML = '<i>Loading preview library...</i>';
        }
    }

    // Initial update
    updatePreview();

    // Listen for changes
    markdownField.addEventListener('input', updatePreview);

    // Check if marked is loaded, if not, wait a bit
    if (typeof marked === 'undefined') {
        setTimeout(updatePreview, 1000);
    }
});
