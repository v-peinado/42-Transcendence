export async function loadHTML(path) {
    const response = await fetch(path);
    if (!response.ok) {
        throw new Error(`Error loading HTML: ${response.status}`);
    }
    return await response.text();
}

export function replaceContent(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = content;
    }
}
