import React, { useState } from 'react'

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:5000'

export default function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState('')

  function onFileChange(e) {
    const f = e.target.files?.[0]
    setResponse(null)
    setError('')
    if (!f) {
      setFile(null)
      setPreview(null)
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setResponse(null)

    if (!file) {
      setError('Please choose an image first.')
      return
    }

    try {
      setLoading(true)
      const form = new FormData()
      form.append('image', file)

      const res = await fetch(`${BACKEND}/detect`, { method: 'POST', body: form })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(`Server error (${res.status}): ${txt}`)
      }
      const data = await res.json()

      // ✅ Build absolute URL (backend now serves at /results/<filename>)
      let annotatedUrl = null
      if (data.image_url) {
        annotatedUrl = `${BACKEND}${data.image_url}`
      }

      setResponse({
        detections: data.detections ?? [],
        image_url: annotatedUrl
      })
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0f172a',
      color: 'white',
      padding: 16
    }}>
      <div style={{
        width: '100%',
        maxWidth: 720,
        background: '#111827',
        borderRadius: 16,
        padding: 24,
        boxShadow: '0 10px 30px rgba(0,0,0,0.25)'
      }}>
        <h1 style={{ margin: 0, fontSize: 24, marginBottom: 12 }}>Waste Detection — Day 9</h1>
        <p style={{ marginTop: 0, opacity: 0.8 }}>
          Upload an image, preview it, and detect waste objects.
        </p>

        <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12 }}>
          <input
            type="file"
            accept="image/*"
            onChange={onFileChange}
            style={{ padding: 8, background: '#0b1220', borderRadius: 8 }}
          />

          {preview && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 14, opacity: 0.8, marginBottom: 6 }}>Preview</div>
              <img
                src={preview}
                alt="preview"
                style={{ maxWidth: '100%', borderRadius: 12, border: '1px solid #1f2937' }}
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !file}
            style={{
              padding: '10px 14px',
              background: loading ? '#374151' : '#2563eb',
              border: 'none',
              borderRadius: 10,
              color: 'white',
              fontWeight: 600,
              cursor: loading || !file ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Detecting…' : 'Detect Waste'}
          </button>
        </form>

        {error && (
          <div style={{
            marginTop: 12,
            background: '#7f1d1d',
            padding: 10,
            borderRadius: 8
          }}>
            {error}
          </div>
        )}

        {response && (
          <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Result</div>

            <pre style={{
              background: '#0b1220',
              padding: 12,
              borderRadius: 8,
              overflow: 'auto'
            }}>
{JSON.stringify(response.detections, null, 2)}
            </pre>

            {response.image_url && (
              <div>
                <div style={{ fontSize: 14, opacity: 0.8, marginBottom: 6 }}>
                  Annotated Image
                </div>
                <img
                  src={response.image_url}
                  alt="annotated result"
                  style={{ maxWidth: '100%', borderRadius: 12, border: '1px solid #1f2937' }}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
