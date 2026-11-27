// Screenshot functionality
async function captureScreenshot(filePath, options = {}) {
    const params = new URLSearchParams({
        n: options.n || 6,
        width: options.width || 1280,
        head: options.head || 5,
        tail: options.tail || 5,
        fmt: options.format || 'jpg',
        zip: options.zip !== false ? '1' : '0'
    });
    
    const res = await fetch(`/api/ss?file=${encodeURIComponent(filePath)}&${params}`);
    const data = await res.json();
    
    if (data.error) {
        alert(data.error);
        return null;
    }
    
    // Create download links
    const container = document.createElement('div');
    container.innerHTML = `
        <h3>Screenshots (${data.params.n} of ${data.meta.duration}s)</h3>
    `;
    
    data.files.forEach((file, i) => {
        const a = document.createElement('a');
        a.href = `/__asp_ss__/${data.base}${file}`;
        a.download = file;
        a.textContent = `Screenshot ${i}`;
        container.appendChild(a);
    });
    
    if (data.zip) {
        const zipLink = document.createElement('a');
        zipLink.href = `/__asp_ss__/${data.base}archive.zip`;
        zipLink.download = 'screenshots.zip';
        zipLink.textContent = 'Download All as ZIP';
        container.appendChild(zipLink);
    }
    
    return container;
}