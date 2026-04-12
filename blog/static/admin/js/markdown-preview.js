function loadMarked() {
    if (window.marked) {
        return Promise.resolve(window.marked);
    }

    return new Promise((resolve, reject) => {
        const existing = document.querySelector('script[data-marked-loader="true"]');
        if (existing) {
            existing.addEventListener('load', () => resolve(window.marked));
            existing.addEventListener('error', reject);
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.async = true;
        script.dataset.markedLoader = 'true';
        script.onload = () => resolve(window.marked);
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function loadMermaid() {
    if (window.mermaid) {
        return Promise.resolve(window.mermaid);
    }

    return new Promise((resolve, reject) => {
        const existing = document.querySelector('script[data-mermaid-loader="true"]');
        if (existing) {
            existing.addEventListener('load', () => resolve(window.mermaid));
            existing.addEventListener('error', reject);
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
        script.async = true;
        script.dataset.mermaidLoader = 'true';
        script.onload = () => resolve(window.mermaid);
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function normalizeMarkdown(markdownText) {
    if (!markdownText) {
        return markdownText;
    }

    const fenceCount = (markdownText.match(/```/g) || []).length;
    if (fenceCount % 2 !== 0) {
        return `${markdownText.trimEnd()}\n\`\`\``;
    }
    return markdownText;
}

function configureMarked() {
    if (!window.marked) {
        return;
    }

    window.marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
    });
}

function renderMarkdown(markdownText) {
    if (!window.marked) {
        return markdownText;
    }

    const normalized = normalizeMarkdown(markdownText);
    return window.marked.parse(normalized);
}

function convertMermaidBlocks(previewRoot) {
    if (!previewRoot) {
        return;
    }

    const mermaidStarters = [
        'graph ',
        'flowchart ',
        'sequenceDiagram',
        'classDiagram',
        'stateDiagram',
        'erDiagram',
        'journey',
        'gantt',
        'pie',
        'mindmap',
        'timeline',
        'quadrantChart',
        'xychart',
        'gitGraph',
    ];

    const nodes = previewRoot.querySelectorAll('pre code');
    nodes.forEach((node) => {
        const rawText = (node.textContent || '').trim();
        const className = node.className || '';
        const isMermaidCode = className.includes('language-mermaid');
        const startsLikeMermaid = mermaidStarters.some((starter) => rawText.startsWith(starter));

        if (!rawText || (!isMermaidCode && !startsLikeMermaid)) {
            return;
        }

        const container = document.createElement('div');
        container.className = 'mermaid';
        container.textContent = rawText;

        const parent = node.closest('pre') || node;
        parent.replaceWith(container);
    });
}

function renderMermaid(previewRoot) {
    if (!window.mermaid || !previewRoot) {
        return;
    }

    convertMermaidBlocks(previewRoot);
    window.mermaid.run({ nodes: previewRoot.querySelectorAll('.mermaid') });
}

function insertAtSelection(textarea, before, after = '') {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = textarea.value.slice(start, end);
    const replacement = `${before}${selected || ''}${after}`;

    textarea.setRangeText(replacement, start, end, 'end');

    if (!selected && after) {
        const cursor = start + before.length;
        textarea.setSelectionRange(cursor, cursor);
    }

    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.focus();
}

function buildToolbar(toolbar, textarea) {
    const actions = [
        { label: 'H', title: 'Titulo', run: () => insertAtSelection(textarea, '## ', '') },
        { label: 'B', title: 'Negrito', run: () => insertAtSelection(textarea, '**', '**') },
        { label: 'I', title: 'Italico', run: () => insertAtSelection(textarea, '*', '*') },
        { label: '"', title: 'Citação', run: () => insertAtSelection(textarea, '> ', '') },
        { label: '</>', title: 'Codigo inline', run: () => insertAtSelection(textarea, '`', '`') },
        { label: '{}', title: 'Bloco de codigo', run: () => insertAtSelection(textarea, '\n```\n', '\n```\n') },
        { label: '[]', title: 'Lista', run: () => insertAtSelection(textarea, '\n- item 1\n- item 2\n', '') },
        { label: '@', title: 'Link', run: () => insertAtSelection(textarea, '[texto](https://)', '') },
        { label: 'M', title: 'Mermaid', run: () => insertAtSelection(textarea, '\n```mermaid\ngraph TD\nA --> B\n', '```\n') },
    ];

    actions.forEach((action) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'markdown-toolbar__button';
        button.textContent = action.label;
        button.title = action.title;
        button.addEventListener('click', action.run);
        toolbar.appendChild(button);
    });
}

function initSplitEditor(root) {
    const textarea = root.querySelector('textarea[data-markdown-editor="true"]');
    const preview = root.querySelector('.markdown-live-preview');
    const toolbar = root.querySelector('[data-markdown-toolbar="true"]');
    const wordCount = root.querySelector('[data-markdown-word-count="true"]');
    const lineCount = root.querySelector('[data-markdown-line-count="true"]');

    if (!textarea || !preview || !toolbar) {
        return;
    }

    buildToolbar(toolbar, textarea);

    const updateCounters = () => {
        const value = textarea.value || '';
        const trimmed = value.trim();

        const words = trimmed ? trimmed.split(/\s+/).length : 0;
        const lines = value ? value.replace(/\n$/, '').split(/\r?\n/).length : 0;

        if (wordCount) {
            wordCount.textContent = String(words);
        }
        if (lineCount) {
            lineCount.textContent = String(lines);
        }
    };

    const updatePreview = () => {
        const value = textarea.value || '';
        updateCounters();

        if (!value.trim()) {
            preview.innerHTML = '<p class="markdown-preview__empty">Digite markdown para ver a previsualizacao.</p>';
            return;
        }

        preview.innerHTML = renderMarkdown(value);
        renderMermaid(preview);
    };

    textarea.addEventListener('input', updatePreview);
    textarea.addEventListener('change', updatePreview);
    updatePreview();
}

document.addEventListener('DOMContentLoaded', () => {
    const roots = document.querySelectorAll('[data-markdown-split-root="true"]');
    if (!roots.length) {
        return;
    }

    Promise.all([loadMarked(), loadMermaid().catch(() => null)])
        .then(() => {
            configureMarked();
            if (window.mermaid) {
                window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
            }
            roots.forEach((root) => initSplitEditor(root));
        })
        .catch(() => {
            roots.forEach((root) => {
                const preview = root.querySelector('.markdown-live-preview');
                if (preview) {
                    preview.innerHTML = '<p class="markdown-preview__error">Nao foi possivel carregar a biblioteca de markdown.</p>';
                }
            });
        });
});
