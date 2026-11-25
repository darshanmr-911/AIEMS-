import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import axios from 'axios'
import { Download, FileText, Pencil, Plus, Search, Trash2, Upload, X } from 'lucide-react'
import { api, getSession } from '../lib/api'

type MaterialType = 'NOTES' | 'ASSIGNMENT' | 'QUESTION_PAPER' | 'LAB_MANUAL' | 'OTHER'
type SubjectOption = {
  id: number
  name: string
  code: string
  semester: number
  semester_number: number
  academic_year: string
}
type Material = {
  id: number
  title: string
  description: string
  material_type: MaterialType
  approval_status: string
  subject: number
  subject_name: string
  subject_code: string
  semester: number
  semester_number: number
  academic_year: string
  created_at: string
  download_count: number
}
type Department = { id: number; code: string; name: string }
type MaterialForm = {
  title: string
  description: string
  material_type: MaterialType
  semester: string
  subject: string
  academic_year: string
}
type Collection<T> = T[] | { results: T[] }

const MATERIAL_TYPES: Array<{ value: MaterialType; label: string }> = [
  { value: 'NOTES', label: 'Notes' },
  { value: 'ASSIGNMENT', label: 'Assignments' },
  { value: 'QUESTION_PAPER', label: 'Question Papers' },
  { value: 'LAB_MANUAL', label: 'Lab Manuals' },
  { value: 'OTHER', label: 'Other' },
]

function collection<T>(data: Collection<T>): T[] {
  return Array.isArray(data) ? data : data.results
}

function errorText(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data
    if (data && typeof data === 'object') {
      const detail = Reflect.get(data, 'detail')
      if (typeof detail === 'string') return detail
      const firstValue = Object.values(data)[0]
      if (typeof firstValue === 'string') return firstValue
      if (Array.isArray(firstValue) && typeof firstValue[0] === 'string') return firstValue[0]
    }
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

function MaterialEditor({
  material,
  subjects,
  department,
  onClose,
  onSaved,
}: {
  material: Material | null
  subjects: SubjectOption[]
  department: Department | null
  onClose: () => void
  onSaved: () => Promise<void>
}) {
  const [form, setForm] = useState<MaterialForm>({
    title: material?.title || '',
    description: material?.description || '',
    material_type: material?.material_type || 'NOTES',
    semester: material ? String(material.semester) : '',
    subject: material ? String(material.subject) : '',
    academic_year: material?.academic_year || '',
  })
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const semesters = useMemo(() => {
    const unique = new Map<number, SubjectOption>()
    subjects.forEach(option => unique.set(option.semester, option))
    return [...unique.values()].sort((a, b) => a.semester_number - b.semester_number)
  }, [subjects])
  const availableSubjects = subjects.filter(option => !form.semester || String(option.semester) === form.semester)

  const updateSemester = (semesterId: string) => {
    const semester = semesters.find(option => String(option.semester) === semesterId)
    setForm({
      ...form,
      semester: semesterId,
      subject: '',
      academic_year: semester?.academic_year || '',
    })
  }

  const updateSubject = (subjectId: string) => {
    const subject = subjects.find(option => String(option.id) === subjectId)
    setForm({
      ...form,
      subject: subjectId,
      semester: subject ? String(subject.semester) : form.semester,
      academic_year: subject?.academic_year || form.academic_year,
    })
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.subject || !form.semester || !form.academic_year) {
      setError('Choose an assigned semester and subject.')
      return
    }
    if (file && file.size > 25 * 1024 * 1024) {
      setError('The file must not exceed 25 MB.')
      return
    }
    setSaving(true)
    setError('')
    const data = new FormData()
    Object.entries(form).forEach(([key, value]) => data.append(key, value))
    if (file) data.append('file', file)
    try {
      if (material) {
        await api.patch(`/teacher/materials/${material.id}/`, data)
      } else {
        if (!file) {
          setError('Choose a PDF, DOCX or PPTX file.')
          return
        }
        await api.post('/teacher/materials/', data)
      }
      await onSaved()
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setSaving(false)
    }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="teacher-material-title" onMouseDown={event => event.stopPropagation()}>
      <div className="modal-heading">
        <div><span>Teacher materials</span><h2 id="teacher-material-title">{material ? 'Edit material' : 'Upload material'}</h2></div>
        <button className="icon-button" onClick={onClose} aria-label="Close"><X size={17}/></button>
      </div>
      <form onSubmit={submit}>
        <div className="form-grid">
          <label className="field"><span>Title</span><input required maxLength={250} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })}/></label>
          <label className="field"><span>Material type</span><select value={form.material_type} onChange={event => setForm({ ...form, material_type: event.target.value as MaterialType })}>{MATERIAL_TYPES.map(type => <option value={type.value} key={type.value}>{type.label}</option>)}</select></label>
          <label className="field"><span>Department</span><input readOnly value={department ? `${department.code} · ${department.name}` : 'Your assigned department'}/></label>
          <label className="field"><span>Semester</span><select required value={form.semester} onChange={event => updateSemester(event.target.value)}><option value="">Choose semester</option>{semesters.map(option => <option value={option.semester} key={option.semester}>Semester {option.semester_number} · {option.academic_year}</option>)}</select></label>
          <label className="field"><span>Subject</span><select required value={form.subject} onChange={event => updateSubject(event.target.value)}><option value="">Choose assigned subject</option>{availableSubjects.map(option => <option value={option.id} key={option.id}>{option.code} · {option.name}</option>)}</select></label>
          <label className="field"><span>Academic year</span><input readOnly required value={form.academic_year} placeholder="Choose a subject"/></label>
          <label className="field span"><span>Description</span><textarea rows={3} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })}/></label>
          <label className="field span"><span>{material ? 'Replace file (optional)' : 'Study material file'}</span><input type="file" accept=".pdf,.docx,.pptx" required={!material} onChange={event => setFile(event.target.files?.[0] || null)}/></label>
        </div>
        <p className="form-hint">Only subjects assigned by your HOD are available. New uploads and edited materials require HOD approval.</p>
        {error && <div className="error-message" role="alert">{error}</div>}
        <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? 'Saving…' : material ? 'Save changes' : 'Upload material'}</button></div>
      </form>
    </section>
  </div>
}

export function TeacherMaterialsContent() {
  const session = getSession()
  const [department, setDepartment] = useState<Department | null>(session?.user.department || null)
  const [subjects, setSubjects] = useState<SubjectOption[]>([])
  const [materials, setMaterials] = useState<Material[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editor, setEditor] = useState<Material | null | undefined>(undefined)
  const [deleteTarget, setDeleteTarget] = useState<Material | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [optionsResponse, materialsResponse] = await Promise.all([
        api.get<{ department: Department; subjects: SubjectOption[] }>('/teacher/materials/options/'),
        api.get<Collection<Material>>('/teacher/materials/', {
          params: { search: search || undefined, approval_status: status || undefined },
        }),
      ])
      setDepartment(optionsResponse.data.department)
      setSubjects(optionsResponse.data.subjects)
      setMaterials(collection(materialsResponse.data))
      setError('')
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setLoading(false)
    }
  }, [search, status])

  useEffect(() => { void load() }, [load])

  const save = async () => {
    setEditor(undefined)
    setNotice(editor ? 'Material updated and sent for approval.' : 'Material uploaded and sent for approval.')
    await load()
  }

  const download = async (material: Material) => {
    try {
      const response = await api.get(`/teacher/materials/${material.id}/download/`, { responseType: 'blob' })
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = material.title.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '')
      link.click()
      URL.revokeObjectURL(url)
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const archive = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setError('')
    try {
      await api.delete(`/teacher/materials/${deleteTarget.id}/`)
      setNotice('Material removed from your list. Its history is preserved for the department.')
      setDeleteTarget(null)
      await load()
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setDeleting(false)
    }
  }

  return <>
    <section className="panel">
      <div className="admin-toolbar">
        <div className="library-search"><Search size={17}/><input aria-label="Search my materials" value={search} onChange={event => { setSearch(event.target.value); setLoading(true) }} placeholder="Search title or subject"/></div>
        <select aria-label="Filter by approval status" value={status} onChange={event => { setStatus(event.target.value); setLoading(true) }}><option value="">All statuses</option><option value="PENDING">Pending</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option></select>
        <button className="button primary" onClick={() => setEditor(null)}><Plus size={16}/> Upload material</button>
      </div>
      {department && <p className="form-hint">{department.code} · {department.name} — uploads are automatically associated with your department.</p>}
      {notice && <div className="success-message" role="status">{notice}</div>}
      {error && <div className="error-message" role="alert">{error}</div>}
      {loading ? <p className="muted-copy">Loading your materials…</p>
        : materials.length ? <div className="table-wrap teacher-material-table"><table><thead><tr><th>Material</th><th>Subject / semester</th><th>Uploaded</th><th>Status</th><th>Downloads</th><th>Actions</th></tr></thead>
          <tbody>{materials.map(material => <tr key={material.id}>
            <td><strong>{material.title}</strong><small className="table-subtext">{MATERIAL_TYPES.find(type => type.value === material.material_type)?.label || material.material_type}</small></td>
            <td>{material.subject_code} · Sem {material.semester_number}<small className="table-subtext">{material.academic_year}</small></td>
            <td>{new Date(material.created_at).toLocaleDateString()}</td>
            <td><span className={`status ${material.approval_status.toLowerCase()}`}>{material.approval_status}</span></td>
            <td>{material.download_count}</td>
            <td><div className="teacher-actions">
              <button className="button secondary compact" aria-label={`Download ${material.title}`} onClick={() => void download(material)}><Download size={14}/></button>
              <button className="button secondary compact" aria-label={`Edit ${material.title}`} onClick={() => setEditor(material)}><Pencil size={14}/></button>
              <button className="button danger compact" aria-label={`Delete ${material.title}`} onClick={() => setDeleteTarget(material)}><Trash2 size={14}/></button>
            </div></td>
          </tr>)}</tbody></table></div>
          : <div className="empty-state"><div><FileText size={22}/></div><h3>{subjects.length ? 'No materials found' : 'No subjects assigned yet'}</h3><p>{subjects.length ? 'Upload a resource or adjust your search and status filters.' : 'Ask your department HOD to assign your subjects before uploading materials.'}</p></div>}
    </section>
    {editor !== undefined && <MaterialEditor material={editor} subjects={subjects} department={department} onClose={() => setEditor(undefined)} onSaved={save}/>}
    {deleteTarget && <div className="modal-backdrop" onMouseDown={() => setDeleteTarget(null)}>
      <section className="modal confirmation-modal" role="dialog" aria-modal="true" aria-labelledby="delete-material-title" onMouseDown={event => event.stopPropagation()}>
        <div className="modal-heading"><div><span>Confirm removal</span><h2 id="delete-material-title">Delete this material?</h2></div><button className="icon-button" onClick={() => setDeleteTarget(null)} aria-label="Close"><X size={17}/></button></div>
        <p>“{deleteTarget.title}” will be archived and removed from your list. The HOD can still access its approval and audit history.</p>
        <div className="modal-actions"><button className="button secondary" onClick={() => setDeleteTarget(null)}>Cancel</button><button className="button danger" disabled={deleting} onClick={() => void archive()}>{deleting ? 'Removing…' : 'Delete material'}</button></div>
      </section>
    </div>}
  </>
}
