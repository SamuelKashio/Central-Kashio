# 🚀 Cómo Subir los Archivos a tu Nuevo Repositorio GitHub

## Archivos Incluidos (Listos para Subir)

```
✅ app.py                    (1,036 líneas - Código principal)
✅ requirements.txt          (Dependencias Python)
✅ .gitignore               (Archivos a ignorar)
✅ README.md                (Documentación)
✅ .streamlit/config.toml    (Configuración Streamlit)
```

---

## 📝 OPCIÓN A: Interfaz Web GitHub (Recomendado - Sin Terminal)

### Paso 1: Crear Nuevo Repositorio

1. Abre **GitHub** con tu cuenta corporativa
2. Click en **"+"** (esquina superior izquierda)
3. Selecciona **"New repository"**
4. Nombre: **`cdr-dashboard`**
5. Descripción: **"Dashboard de Central Telefónica - CallMyWay"**
6. Visibility: **"Private"** (según tu política corporativa)
7. **NO** inicialices con README (ya lo tenemos)
8. Click **"Create repository"**

### Paso 2: Subir Archivos Desde Interface Web

1. En tu nuevo repo vacío, click en **"Add file"** → **"Upload files"**

2. **Copia-pega o arrastra los siguientes archivos:**

   ```
   app.py
   requirements.txt
   README.md
   .gitignore
   ```

3. Si tienes `.streamlit/config.toml`:
   - Primero crea la carpeta `.streamlit`
   - Luego sube `config.toml` dentro

4. En el campo **"Commit message"** escribe:
   ```
   Initial commit: Dashboard CallMyWay v7.0 - Producción
   ```

5. Click **"Commit changes"**

### Paso 3: Verificar en GitHub

Deberías ver en tu repo:
```
cdr-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

---

## 💻 OPCIÓN B: Terminal Git (Si tienes acceso local)

### Paso 1: Clonar Nuevo Repositorio

```bash
git clone https://github.com/tu-usuario-corporativo/cdr-dashboard.git
cd cdr-dashboard
```

### Paso 2: Copiar Archivos

Copia estos archivos en la carpeta `cdr-dashboard`:

```bash
# Copiar los 4 archivos principales
cp app.py .
cp requirements.txt .
cp .gitignore .
cp README.md .

# Copiar configuración Streamlit
mkdir -p .streamlit
cp .streamlit/config.toml .streamlit/
```

### Paso 3: Hacer Commit y Push

```bash
# Ver estado
git status

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit: Dashboard CallMyWay v7.0 - Producción"

# Subir a GitHub
git push origin main
```

---

## 🔑 PASO IMPORTANTE: Configurar Secrets en Streamlit Cloud

**Después de subir a GitHub**, configura los secretos:

### 1. Ve a Streamlit Cloud

```
https://share.streamlit.io
```

### 2. Manage App

- Abre tu dashboard
- Click en **"⋮"** (esquina superior derecha)
- Selecciona **"Manage app"**

### 3. Settings → Secrets

```
Click en la pestaña "Settings"
Luego "Secrets"
```

### 4. Agregar Credenciales

En el editor de Secrets, pega:

```toml
CMW_USER = "tu_usuario_callmyway"
CMW_PASS = "tu_contraseña_callmyway"
```

### 5. Guardar

Click en **"Save"** → La app se recargará automáticamente

---

## ✅ Verificación

Una vez completado, deberías tener:

- [ ] Repositorio creado en GitHub corporativo
- [ ] 5 archivos subidos (app.py, requirements.txt, .gitignore, README.md, .streamlit/config.toml)
- [ ] Secrets configurados en Streamlit Cloud (CMW_USER, CMW_PASS)
- [ ] Dashboard desplegado y funcionando

### Prueba Rápida:

Abre tu dashboard en:
```
https://share.streamlit.io/tu-empresa/cdr-dashboard
```

Deberías ver:
- ✅ Las 8 pestañas cargando
- ✅ Datos fluyendo desde CallMyWay
- ✅ Gráficos renderizándose
- ✅ Sin errores de credenciales

---

## 🔄 De Ahora en Adelante: Hacer Cambios

**El flujo es muy simple:**

```
1. Abre GitHub → cdr-dashboard → app.py
2. Click en el ✏️ (Edit)
3. Haz cambios
4. Commit directamente
5. Streamlit Cloud redeploy automático (2-3 min)
```

**Sin necesidad de terminal local**

---

## 🆘 Si Algo Falla

### "Archivo no se subió correctamente"
- Verifica que el archivo tenga la extensión correcta
- Intenta subir desde otra pestaña del navegador
- Usa GitHub Desktop si es más fácil

### "GitHub me pide autenticación"
- Usa token de GitHub (en Settings → Developer settings)
- O configura SSH key
- Consulta docs de GitHub para más detalles

### "Dashboard no carga en Streamlit"
- Ve a "Manage app" → "View logs"
- Busca el error específico
- Verifica Secrets en Settings

### "Cambios no aparecen"
- Espera 3 minutos (tiempo de redeploy)
- Hard refresh: `Ctrl+Shift+R`
- Verifica los logs en Streamlit Cloud

---

## 📊 Estructura Final

Una vez completado, tu repositorio verá así:

```
tu-empresa/cdr-dashboard
├── .gitignore              ← Protege credenciales
├── .streamlit/
│   └── config.toml         ← Configuración visual
├── app.py                  ← 1,036 líneas - Código principal
├── requirements.txt        ← 4 librerías necesarias
└── README.md               ← Documentación completa
```

---

## 🎯 Próximo Paso

Una vez en GitHub y Streamlit Cloud:

1. Solicita en Claude corporativo mejoras al dashboard
2. Recibe código actualizado
3. Edita `app.py` en GitHub web
4. Commit changes
5. Streamlit redeploy automático ✅

---

## 📞 Resumen Rápido

| Acción | Cómo |
|--------|------|
| Crear repo | GitHub → + → New repository |
| Subir archivos | "Add file" → "Upload files" |
| Configurar secrets | Streamlit Cloud → Manage app → Settings → Secrets |
| Hacer cambios | GitHub → Edit file → Commit |
| Ver cambios | Esperar 3 min + refresh |

---

**¡Listo! Tu dashboard está en GitHub corporativo y Streamlit Cloud.** ☁️🚀

