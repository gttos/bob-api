import re

with open('app/static/index.html', 'r') as f:
    content = f.read()

# Make selectImage show large image
content = content.replace("document.getElementById('treeTitle').textContent", "document.getElementById('mainImage').src = img.url;\n  document.getElementById('mainImage').ondblclick = () => openLightbox(img.url);\n  document.getElementById('treeTitle').textContent")

# Update uploadFile
upload_file_new = """async function uploadFile(file, spaceId = '') {
  if (!file || !currentProject) return;
  const form = new FormData(); form.append('file', file);
  let url = `${API}/projects/${currentProject}/images`;
  if (spaceId) url += `?space_id=${spaceId}`;
  const res = await fetch(url, { method:'POST', body:form });
  if (res.ok) loadGallery();
}"""
content = re.sub(r'async function uploadFile\(file\) \{.*?\n\}', upload_file_new, content, flags=re.DOTALL)


# Update loadGallery
load_gallery_new = """// Spaces Management
async function createSpace() {
  const nameInput = document.getElementById('newSpaceName');
  const name = nameInput.value.trim();
  if (!name || !currentProject) return;

  await fetch(`${API}/projects/${currentProject}/spaces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name })
  });

  nameInput.value = '';
  loadGallery();
}

async function deleteSpace(spaceId) {
  if (!confirm('¿Eliminar este espacio? Las imágenes se mantendrán.')) return;
  await fetch(`${API}/spaces/${spaceId}`, { method: 'DELETE' });
  loadGallery();
}

async function loadGallery() {
  if (!currentProject) return;

  // Fetch spaces for this project
  const spacesRes = await fetch(`${API}/projects/${currentProject}/spaces`);
  const spaces = spacesRes.ok ? await spacesRes.json() : [];

  const res = await fetch(`${API}/projects/${currentProject}/images?page=1&page_size=100`);
  const d = await res.json(); galleryData = d.items;
  document.getElementById('imgCount').textContent = `(${d.total})`;
  const container = document.getElementById('galleryTree');

  let html = `<div class="flex" style="margin-bottom:10px; padding:8px;">
    <input type="text" id="newSpaceName" placeholder="Nombre del espacio..." style="flex:1;">
    <button onclick="createSpace()">Crear espacio</button>
  </div>`;

  const originals = d.items.filter(i => i.type === 'original' && !i.parent_image_id);
  const generated = d.items.filter(i => i.type !== 'original' || i.parent_image_id);

  if (originals.length === 0 && generated.length === 0) {
    html += '<p style="color:#333;font-size:0.75rem;padding:8px;">No hay imágenes. Crea un espacio y sube una.</p>';
    container.innerHTML = html;
    return;
  }

  const spacesMap = { 'null': { id: null, name: 'Sin espacio', images: [] } };
  spaces.forEach(s => spacesMap[s.id] = { ...s, images: [] });

  originals.forEach(i => {
    const sId = i.space_id || 'null';
    if (spacesMap[sId]) {
      i.children = generated.filter(g => g.parent_image_id === i.id);
      spacesMap[sId].images.push(i);
    }
  });

  Object.values(spacesMap).forEach(space => {
    if (space.id === null && space.images.length === 0) return;

    html += `<div class="tree-group">`;
    html += `<div style="font-size:0.8rem;color:#ccc;font-weight:bold;margin:8px 8px 4px 8px;display:flex;justify-content:space-between;align-items:center;">
      <span>📁 ${space.name}</span>
      ${space.id ? `<button class="sm" style="background:#dc2626;padding:2px 5px;font-size:0.6rem;" onclick="deleteSpace('${space.id}')">✕</button>` : ''}
    </div>`;

    space.images.forEach(orig => {
      const isSel = orig.id === currentImageId ? ' active' : '';
      html += `<div class="tree-parent${isSel}" onclick="selectImage(galleryData.find(i=>i.id==='${orig.id}'))">
        <img src="${orig.thumbnail_url || orig.url}" ondblclick="event.stopPropagation();openLightbox('${orig.url}')">
        <div class="info">
          <div class="name">${orig.filename.length > 18 ? orig.filename.substring(0,18)+'...' : orig.filename}</div>
          <div>${orig.width}×${orig.height}</div>
        </div>
        <button class="sm" style="background:#dc2626;padding:2px 5px;font-size:0.6rem;" onclick="event.stopPropagation();deleteImage('${orig.id}')" title="Eliminar">✕</button>
      </div>`;

      if (orig.children && orig.children.length > 0) {
        html += `<div class="tree-children">`;
        orig.children.forEach(child => {
          const isChildSel = child.id === currentImageId ? ' active' : '';
          html += `<div class="tree-child${isChildSel}" onclick="selectImage(galleryData.find(i=>i.id==='${child.id}'))">
            <span style="color:#666;">└─</span>
            <img src="${child.thumbnail_url || child.url}" style="width:30px;height:24px;object-fit:cover;border-radius:2px;margin:0 4px;" ondblclick="event.stopPropagation();openLightbox('${child.url}')">
            <div class="info" style="font-size:0.65rem;">
              <span class="tag">GEN</span> ${child.filename.substring(0,15)}
            </div>
            <button class="sm" style="background:#dc2626;padding:2px 5px;font-size:0.6rem;margin-left:auto;" onclick="event.stopPropagation();deleteImage('${child.id}')">✕</button>
          </div>`;
        });
        html += `</div>`;
      }
    });

    html += `<div class="drop-zone" onclick="document.getElementById('fileSpace${space.id || 'null'}').click()" ondragover="event.preventDefault(); this.classList.add('dragover')" ondragleave="this.classList.remove('dragover')" ondrop="event.preventDefault(); this.classList.remove('dragover'); uploadFile(event.dataTransfer.files[0], '${space.id || ''}')">
      Subir imagen aquí
      <input type="file" id="fileSpace${space.id || 'null'}" hidden accept="image/*" onchange="if(this.files[0]) uploadFile(this.files[0], '${space.id || ''}')">
    </div>`;

    html += `</div>`;
  });

  container.innerHTML = html;
}"""
content = re.sub(r'async function loadGallery\(\) \{.*?\nfunction selectImage', load_gallery_new + '\n\nfunction selectImage', content, flags=re.DOTALL)

with open('app/static/index.html', 'w') as f:
    f.write(content)
