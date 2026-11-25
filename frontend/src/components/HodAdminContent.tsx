import { useCallback, useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import axios from 'axios'
import {
  ArrowRight, Archive, BookOpen, CalendarDays, Check, ClipboardList,
  Download, FileText, Plus, RefreshCw, Search, ShieldCheck, Upload,
  UserPlus, Users, X,
} from 'lucide-react'
import { api } from '../lib/api'

type DepartmentInfo = { id: number; code: string; name: string }
type DashboardData = {
  department: DepartmentInfo
  hod: { email: string; name: string }
  students: number
  teachers: number
  assigned_subjects: number
  subjects: number
  materials: number
  total_uploaded_materials: number
  pending_materials: number
  approved_materials: number
  recent_materials: Material[]
  recent_teacher_activity: Activity[]
}
type Activity = {
  id: number
  action: string
  actor: string
  target: string
  created_at: string
  details: Record<string, unknown>
}
type Teacher = {
  id: number
  teacher_profile_id: number
  first_name: string
  last_name: string
  email: string
  is_active: boolean
  employee_id: string
  designation: string
  department_name: string
  assigned_subjects: Array<{
    id: number
    subject_id: number
    subject_name: string
    subject_code: string
    semester_id: number
    semester_number: number
    academic_year: string
  }>
}
type TeacherUpload = {
  id: number
  title: string
  category: string
  approval_status: string
  uploaded_at: string
  download_count: number
}
type Semester = {
  id: number
  semester_number: number
  academic_year: string
}
type Subject = {
  id: number
  subject_name: string
  subject_code: string
  semester: number
}
type Assignment = {
  id: number
  teacher: number
  teacher_name: string
  subject: number
  subject_name: string
  subject_code: string
  semester_number: number
  academic_year: string
}
type Material = {
  id: number
  title: string
  description?: string
  category: string
  approval_status: string
  subject_name: string
  subject_code: string
  uploaded_by_name: string
  uploaded_at: string
  download_count: number
  semester: number
  subject: number
  module: number | null
  academic_year: string
}
type Account = {
  id: number
  first_name: string
  last_name: string
  email: string
  department_name: string
  department_code: string
}
type TeacherForm = {
  first_name: string
  last_name: string
  email: string
  employee_id: string
  designation: string
  password: string
  password_confirm: string
}
type Collection<T> = T[] | { results: T[] }

function collection<T>(data: Collection<T>): T[] {
  return Array.isArray(data) ? data : data.results
}

function errorText(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data
    if (typeof data === 'string') return data
    if (data && typeof data === 'object') {
      const detail = 'detail' in data ? data.detail : undefined
      if (typeof detail === 'string') return detail
      const firstValue = Object.values(data)[0]
      if (typeof firstValue === 'string') return firstValue
      if (Array.isArray(firstValue) && typeof firstValue[0] === 'string') return firstValue[0]
    }
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>
}

function PanelHeading({ title, action }: { title: string; action?: ReactNode }) {
  return <div className="panel-heading"><h2>{title}</h2>{action}</div>
}

function ErrorNotice({ children }: { children: string }) {
  return <div className="error-message" role="alert">{children}</div>
}

function EmptyNotice({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><div><FileText size={22}/></div><h3>{title}</h3><p>{text}</p></div>
}

function Stat({ label, value, detail, tone }: {
  label: string
  value: string | number
  detail: string
  tone: 'blue' | 'green' | 'amber' | 'red'
}) {
  return <article className="stat-card">
    <div className={`stat-icon ${tone}`}><ClipboardList size={18}/></div>
    <div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>
  </article>
}

function formatAction(action: string) {
  return action.replaceAll('.', ' ').replaceAll('_', ' ')
}

export function HodDashboardContent() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<DashboardData>('/hod/dashboard/')
      .then((response) => setData(response.data))
      .catch((reason: unknown) => setError(errorText(reason)))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="stat-grid four">{[1, 2, 3, 4].map((item) => <div className="stat-card skeleton" key={item}/>)}</div>
  if (error || !data) return <ErrorNotice>{error || 'Department dashboard is unavailable.'}</ErrorNotice>

  return <>
    <section className="welcome-banner hod-welcome">
      <div>
        <span>{data.department.code} · Department administration</span>
        <h2>{data.department.name}</h2>
        <p>{data.hod.email} · Department-only access</p>
      </div>
      <div className="welcome-mark"><ShieldCheck size={34}/></div>
    </section>
    <div className="stat-grid four">
      <Stat label="Teachers" value={data.teachers} detail="In your department" tone="blue"/>
      <Stat label="Assigned subjects" value={data.assigned_subjects} detail="Across teacher assignments" tone="green"/>
      <Stat label="Uploaded materials" value={data.total_uploaded_materials} detail="Department resources" tone="amber"/>
      <Stat label="Pending approvals" value={data.pending_materials} detail={`${data.approved_materials} approved`} tone="red"/>
    </div>
    <div className="dashboard-grid hod-grid">
      <section className="panel">
        <PanelHeading title="Administration workspace"/>
        <div className="hod-shortcuts">
          <a href="/hod/teachers"><Users/><span><strong>Teacher management</strong><small>Add, edit and deactivate teachers</small></span><ArrowRight/></a>
          <a href="/hod/subjects"><BookOpen/><span><strong>Subject management</strong><small>Maintain department subjects and semesters</small></span><ArrowRight/></a>
          <a href="/hod/assignments"><ClipboardList/><span><strong>Teacher assignments</strong><small>Assign subjects and academic years</small></span><ArrowRight/></a>
          <a href="/hod/materials"><FileText/><span><strong>Study materials</strong><small>Upload resources and review submissions</small></span><ArrowRight/></a>
          <a href="/hod/approvals"><Check/><span><strong>Material approvals</strong><small>Review resources awaiting approval</small></span><ArrowRight/></a>
        </div>
      </section>
      <section className="panel">
        <PanelHeading title="Recent department activity"/>
        {data.recent_teacher_activity.length ? <div className="audit-list">
          {data.recent_teacher_activity.slice(0, 6).map((activity) => <article key={activity.id}>
            <span className="audit-dot"/>
            <div><strong>{activity.target || activity.actor}</strong><p>{formatAction(activity.action)}</p><small>{new Date(activity.created_at).toLocaleString()}</small></div>
          </article>)}
        </div> : <EmptyNotice title="No activity yet" text="Teacher and material activity will appear here."/>}
      </section>
    </div>
    <section className="panel">
      <PanelHeading title="Recently uploaded materials" action={<a href="/hod/materials">Open materials <ArrowRight size={14}/></a>}/>
      {data.recent_materials.length ? <div className="table-wrap"><table><thead><tr><th>Material</th><th>Subject</th><th>Uploaded by</th><th>Status</th><th>Uploaded</th></tr></thead>
        <tbody>{data.recent_materials.map((material) => <tr key={material.id}>
          <td><strong>{material.title}</strong></td><td>{material.subject_name}</td><td>{material.uploaded_by_name}</td>
          <td><span className={`status ${material.approval_status.toLowerCase()}`}>{material.approval_status}</span></td>
          <td>{new Date(material.uploaded_at).toLocaleDateString()}</td>
        </tr>)}</tbody></table></div> : <EmptyNotice title="No materials yet" text="Department materials will be listed here."/>}
    </section>
  </>
}

function TeacherEditor({ teacher, onClose, onSaved }: {
  teacher: Teacher | null
  onClose: () => void
  onSaved: (form: TeacherForm, teacher: Teacher | null) => Promise<void>
}) {
  const [form, setForm] = useState<TeacherForm>({
    first_name: teacher?.first_name || '',
    last_name: teacher?.last_name || '',
    email: teacher?.email || '',
    employee_id: teacher?.employee_id || '',
    designation: teacher?.designation || 'Teacher',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await onSaved(form, teacher)
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setSaving(false)
    }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="teacher-editor-title" onMouseDown={(event) => event.stopPropagation()}>
      <div className="modal-heading"><div><span>Department staff</span><h2 id="teacher-editor-title">{teacher ? 'Edit teacher' : 'Add teacher'}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={17}/></button></div>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="First name"><input required value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })}/></Field>
          <Field label="Last name"><input required value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })}/></Field>
          <Field label="Official email"><input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}/></Field>
          <Field label="Employee ID"><input required value={form.employee_id} onChange={(event) => setForm({ ...form, employee_id: event.target.value })}/></Field>
          <Field label="Designation"><input required value={form.designation} onChange={(event) => setForm({ ...form, designation: event.target.value })}/></Field>
          {!teacher && <>
            <Field label="Initial password"><input type="password" required minLength={8} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })}/></Field>
            <Field label="Confirm password"><input type="password" required minLength={8} value={form.password_confirm} onChange={(event) => setForm({ ...form, password_confirm: event.target.value })}/></Field>
          </>}
        </div>
        <p className="form-hint">Department is assigned automatically from your HOD account.</p>
        {error && <ErrorNotice>{error}</ErrorNotice>}
        <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? 'Saving…' : teacher ? 'Save changes' : 'Create teacher'}</button></div>
      </form>
    </section>
  </div>
}

function TeacherDetails({ teacher, onClose }: { teacher: Teacher; onClose: () => void }) {
  const [uploads, setUploads] = useState<TeacherUpload[]>([])
  const [uploadError, setUploadError] = useState('')
  const [uploadsLoading, setUploadsLoading] = useState(true)

  useEffect(() => {
    let active = true
    api.get<TeacherUpload[]>(`/hod/teachers/${teacher.id}/uploads/`)
      .then((response) => { if (active) setUploads(response.data) })
      .catch((reason: unknown) => { if (active) setUploadError(errorText(reason)) })
      .finally(() => { if (active) setUploadsLoading(false) })
    return () => { active = false }
  }, [teacher.id])

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="teacher-details-title" onMouseDown={(event) => event.stopPropagation()}>
      <div className="modal-heading"><div><span>Teacher profile</span><h2 id="teacher-details-title">{teacher.first_name} {teacher.last_name}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={17}/></button></div>
      <dl className="teacher-details">
        <div><dt>Employee ID</dt><dd>{teacher.employee_id}</dd></div><div><dt>Email</dt><dd>{teacher.email}</dd></div>
        <div><dt>Designation</dt><dd>{teacher.designation}</dd></div><div><dt>Account status</dt><dd>{teacher.is_active ? 'Active' : 'Inactive'}</dd></div>
      </dl>
      <h3>Assigned subjects</h3>
      {teacher.assigned_subjects.length ? <div className="teacher-chip-list">{teacher.assigned_subjects.map((assignment) => <span className="teacher-chip" key={assignment.id}>{assignment.subject_code} · Sem {assignment.semester_number} · {assignment.academic_year}</span>)}</div> : <p className="muted-copy">No subjects assigned yet.</p>}
      <h3>Recent uploads</h3>
      {uploadsLoading ? <p className="muted-copy">Loading upload history…</p>
        : uploadError ? <ErrorNotice>{uploadError}</ErrorNotice>
          : uploads.length ? <div className="teacher-upload-history">{uploads.map((upload) => <article key={upload.id}>
            <div><strong>{upload.title}</strong><small>{upload.category.replaceAll('_', ' ').toLowerCase()} · {new Date(upload.uploaded_at).toLocaleDateString()}</small></div>
            <span className={`status ${upload.approval_status.toLowerCase()}`}>{upload.approval_status}</span>
          </article>)}</div>
            : <p className="muted-copy">This teacher has no uploads yet.</p>}
      <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Close</button></div>
    </section>
  </div>
}

export function HodTeachersContent() {
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [search, setSearch] = useState('')
  const [subject, setSubject] = useState('')
  const [active, setActive] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editor, setEditor] = useState<Teacher | null | undefined>(undefined)
  const [details, setDetails] = useState<Teacher | null>(null)
  const [deactivating, setDeactivating] = useState<Teacher | null>(null)
  const [notice, setNotice] = useState('')

  const load = useCallback(async () => {
    try {
      const params = {
        search: search || undefined,
        subject: subject || undefined,
        is_active: active || undefined,
      }
      const [teacherResponse, subjectResponse] = await Promise.all([
        api.get<Collection<Teacher>>('/hod/teachers/', { params }),
        api.get<Collection<Subject>>('/hod/subjects/'),
      ])
      setError('')
      setTeachers(collection(teacherResponse.data))
      setSubjects(collection(subjectResponse.data))
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setLoading(false)
    }
  }, [search, subject, active])

  useEffect(() => { void load() }, [load])

  const saveTeacher = async (form: TeacherForm, teacher: Teacher | null) => {
    if (teacher) {
      await api.patch(`/hod/teachers/${teacher.id}/`, {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        employee_id: form.employee_id,
        designation: form.designation,
      })
    } else {
      await api.post('/hod/teachers/', form)
    }
    setEditor(undefined)
    await load()
  }

  const setStatus = async (teacher: Teacher, isActive: boolean) => {
    await api.patch(`/hod/teachers/${teacher.id}/status/`, { is_active: isActive })
    setDeactivating(null)
    setNotice(isActive ? 'Teacher account activated.' : 'Teacher account deactivated.')
    await load()
  }

  const resetPassword = async (teacher: Teacher) => {
    setNotice('')
    try {
      const response = await api.post<{ detail: string }>(`/hod/teachers/${teacher.id}/reset-password/`)
      setNotice(response.data.detail)
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  return <>
    <section className="panel">
      <div className="admin-toolbar">
        <div className="library-search"><Search size={17}/><input aria-label="Search teachers" value={search} onChange={(event) => { setLoading(true); setSearch(event.target.value) }} placeholder="Search name, email or employee ID"/></div>
        <select aria-label="Filter by subject" value={subject} onChange={(event) => { setLoading(true); setSubject(event.target.value) }}><option value="">All subjects</option>{subjects.map((item) => <option value={item.id} key={item.id}>{item.subject_code} · {item.subject_name}</option>)}</select>
        <select aria-label="Filter by account status" value={active} onChange={(event) => { setLoading(true); setActive(event.target.value) }}><option value="">All account statuses</option><option value="true">Active</option><option value="false">Inactive</option></select>
        <button className="button primary" onClick={() => setEditor(null)}><UserPlus size={16}/> Add teacher</button>
      </div>
      {notice && <div className="success-message" role="status">{notice}</div>}
      {error && <ErrorNotice>{error}</ErrorNotice>}
      {loading ? <div className="table-wrap"><p className="muted-copy">Loading teachers…</p></div>
        : teachers.length ? <div className="table-wrap"><table><thead><tr><th>Teacher</th><th>Employee ID</th><th>Email</th><th>Assigned subjects</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>{teachers.map((teacher) => <tr key={teacher.id}>
            <td><strong>{teacher.first_name} {teacher.last_name}</strong><small className="table-subtext">{teacher.designation}</small></td>
            <td>{teacher.employee_id}</td><td>{teacher.email}</td>
            <td>{teacher.assigned_subjects.length ? teacher.assigned_subjects.map((item) => item.subject_code).join(', ') : '—'}</td>
            <td><span className={`status ${teacher.is_active ? 'approved' : 'rejected'}`}>{teacher.is_active ? 'Active' : 'Inactive'}</span></td>
            <td><div className="teacher-actions">
              <button className="button secondary compact" onClick={() => setDetails(teacher)}>View</button>
              <button className="button secondary compact" onClick={() => setEditor(teacher)}>Edit</button>
              <button className="button secondary compact" onClick={() => void resetPassword(teacher)}><RefreshCw size={13}/> Reset</button>
              {teacher.is_active
                ? <button className="button danger compact" onClick={() => setDeactivating(teacher)}>Deactivate</button>
                : <button className="button secondary compact" onClick={() => void setStatus(teacher, true)}>Activate</button>}
            </div></td>
          </tr>)}</tbody></table></div>
        : <EmptyNotice title="No teachers found" text="Add a teacher or adjust your search filters."/>}
    </section>
    {editor !== undefined && <TeacherEditor teacher={editor} onClose={() => setEditor(undefined)} onSaved={saveTeacher}/>}
    {details && <TeacherDetails teacher={details} onClose={() => setDetails(null)}/>}
    {deactivating && <div className="modal-backdrop" onMouseDown={() => setDeactivating(null)}>
      <section className="modal confirmation-modal" role="dialog" aria-modal="true" aria-labelledby="deactivate-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-heading"><div><span>Confirm account change</span><h2 id="deactivate-title">Deactivate {deactivating.first_name}?</h2></div><button className="icon-button" onClick={() => setDeactivating(null)} aria-label="Close"><X size={17}/></button></div>
        <p>This disables the teacher’s account without deleting their uploads or assignment history.</p>
        <div className="modal-actions"><button className="button secondary" onClick={() => setDeactivating(null)}>Cancel</button><button className="button danger" onClick={() => void setStatus(deactivating, false)}>Deactivate teacher</button></div>
      </section>
    </div>}
  </>
}

export function HodSubjectsContent() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ subject_name: '', subject_code: '', semester: '' })
  const [semesterForm, setSemesterForm] = useState({ semester_number: '', academic_year: '' })

  const load = useCallback(async () => {
    try {
      const [subjectResponse, semesterResponse] = await Promise.all([
        api.get<Collection<Subject>>('/hod/subjects/'),
        api.get<Collection<Semester>>('/hod/semesters/'),
      ])
      setError('')
      setSubjects(collection(subjectResponse.data))
      setSemesters(collection(semesterResponse.data))
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const createSemester = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      await api.post('/hod/semesters/', {
        semester_number: Number(semesterForm.semester_number),
        academic_year: semesterForm.academic_year,
      })
      setSemesterForm({ semester_number: '', academic_year: '' })
      setNotice('Semester created.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const createSubject = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      await api.post('/hod/subjects/', { ...form, semester: Number(form.semester) })
      setForm({ subject_name: '', subject_code: '', semester: '' })
      setNotice('Subject created.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  return <>
    <div className="dashboard-grid hod-grid">
      <section className="panel">
        <PanelHeading title="Add subject"/>
        <form className="form-grid" onSubmit={createSubject}>
          <Field label="Subject name"><input required value={form.subject_name} onChange={(event) => setForm({ ...form, subject_name: event.target.value })}/></Field>
          <Field label="Subject code"><input required value={form.subject_code} onChange={(event) => setForm({ ...form, subject_code: event.target.value })}/></Field>
          <Field label="Semester"><select required value={form.semester} onChange={(event) => setForm({ ...form, semester: event.target.value })}><option value="">Choose semester</option>{semesters.map((item) => <option key={item.id} value={item.id}>Semester {item.semester_number} · {item.academic_year}</option>)}</select></Field>
          <div className="form-actions"><button className="button primary"><Plus size={16}/> Create subject</button></div>
        </form>
      </section>
      <section className="panel">
        <PanelHeading title="Add semester"/>
        <form className="form-grid" onSubmit={createSemester}>
          <Field label="Semester number"><select required value={semesterForm.semester_number} onChange={(event) => setSemesterForm({ ...semesterForm, semester_number: event.target.value })}><option value="">Choose</option>{[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <option key={n} value={n}>{n}</option>)}</select></Field>
          <Field label="Academic year"><input required pattern="[0-9]{4}-[0-9]{4}" placeholder="2025-2026" value={semesterForm.academic_year} onChange={(event) => setSemesterForm({ ...semesterForm, academic_year: event.target.value })}/></Field>
          <div className="form-actions"><button className="button secondary"><CalendarDays size={16}/> Add semester</button></div>
        </form>
      </section>
    </div>
    {notice && <div className="success-message" role="status">{notice}</div>}
    {error && <ErrorNotice>{error}</ErrorNotice>}
    <section className="panel"><PanelHeading title="Department subjects"/>
      {loading ? <p className="muted-copy">Loading subjects…</p> : subjects.length ? <div className="table-wrap"><table><thead><tr><th>Subject</th><th>Code</th><th>Semester</th></tr></thead>
        <tbody>{subjects.map((subject) => {
          const semester = semesters.find((item) => item.id === subject.semester)
          return <tr key={subject.id}><td>{subject.subject_name}</td><td><strong>{subject.subject_code}</strong></td><td>{semester ? `Semester ${semester.semester_number} · ${semester.academic_year}` : '—'}</td></tr>
        })}</tbody></table></div> : <EmptyNotice title="No subjects yet" text="Add a semester and subject to begin assigning teachers."/>}
    </section>
  </>
}

export function HodAssignmentsContent() {
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [teacher, setTeacher] = useState('')
  const [subject, setSubject] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [teacherResponse, subjectResponse, semesterResponse, assignmentResponse] = await Promise.all([
        api.get<Collection<Teacher>>('/hod/teachers/'),
        api.get<Collection<Subject>>('/hod/subjects/'),
        api.get<Collection<Semester>>('/hod/semesters/'),
        api.get<Collection<Assignment>>('/hod/assignments/'),
      ])
      setError('')
      setTeachers(collection(teacherResponse.data).filter((item) => item.is_active))
      setSubjects(collection(subjectResponse.data))
      setSemesters(collection(semesterResponse.data))
      setAssignments(collection(assignmentResponse.data))
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const assignSubject = async (event: FormEvent) => {
    event.preventDefault()
    const selectedTeacher = teachers.find((item) => item.id === Number(teacher))
    const selectedSubject = subjects.find((item) => item.id === Number(subject))
    const selectedSemester = semesters.find((item) => item.id === selectedSubject?.semester)
    if (!selectedTeacher || !selectedSubject || !selectedSemester) return
    setError('')
    setNotice('')
    try {
      await api.post('/hod/assignments/', {
        teacher: selectedTeacher.teacher_profile_id,
        subject: selectedSubject.id,
        academic_year: selectedSemester.academic_year,
      })
      setNotice('Subject assigned to teacher.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const removeAssignment = async (assignment: Assignment) => {
    if (!window.confirm(`Remove ${assignment.subject_code} from ${assignment.teacher_name}?`)) return
    setError('')
    try {
      await api.delete(`/hod/assignments/${assignment.id}/`)
      setNotice('Assignment removed.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  return <>
    <section className="panel">
      <PanelHeading title="Assign a subject"/>
      <form className="admin-toolbar assignment-toolbar" onSubmit={assignSubject}>
        <select required aria-label="Teacher" value={teacher} onChange={(event) => setTeacher(event.target.value)}><option value="">Choose teacher</option>{teachers.map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name} · {item.employee_id}</option>)}</select>
        <select required aria-label="Subject" value={subject} onChange={(event) => setSubject(event.target.value)}><option value="">Choose subject</option>{subjects.map((item) => <option key={item.id} value={item.id}>{item.subject_code} · {item.subject_name}</option>)}</select>
        <button className="button primary"><Plus size={16}/> Assign subject</button>
      </form>
      <p className="form-hint">Academic year is taken from the subject’s semester and cannot be changed here.</p>
      {notice && <div className="success-message" role="status">{notice}</div>}
      {error && <ErrorNotice>{error}</ErrorNotice>}
    </section>
    <section className="panel"><PanelHeading title="Current assignments"/>
      {loading ? <p className="muted-copy">Loading assignments…</p> : assignments.length ? <div className="table-wrap"><table><thead><tr><th>Teacher</th><th>Subject</th><th>Semester</th><th>Academic year</th><th></th></tr></thead>
        <tbody>{assignments.map((item) => <tr key={item.id}><td>{item.teacher_name}</td><td>{item.subject_code} · {item.subject_name}</td><td>{item.semester_number}</td><td>{item.academic_year}</td><td><button className="button danger compact" onClick={() => void removeAssignment(item)}>Remove</button></td></tr>)}</tbody></table></div>
        : <EmptyNotice title="No assignments yet" text="Choose a teacher and subject above to create the first assignment."/>}
    </section>
  </>
}

function MaterialUpload({ semesters, subjects, onClose, onUploaded }: {
  semesters: Semester[]
  subjects: Subject[]
  onClose: () => void
  onUploaded: () => Promise<void>
}) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    semester: '',
    subject: '',
    module: '',
    category: 'NOTES',
    academic_year: '',
  })
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!file) {
      setError('Choose a PDF, DOCX or PPTX file.')
      return
    }
    setSaving(true)
    setError('')
    const data = new FormData()
    Object.entries(form).forEach(([key, value]) => {
      if (value) data.append(key, value)
    })
    data.append('file', file)
    try {
      await api.post('/hod/materials/', data, { headers: { 'Content-Type': 'multipart/form-data' } })
      await onUploaded()
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setSaving(false)
    }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="material-upload-title" onMouseDown={(event) => event.stopPropagation()}>
      <div className="modal-heading"><div><span>Department library</span><h2 id="material-upload-title">Upload study material</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={17}/></button></div>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="Title"><input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })}/></Field>
          <Field label="Category"><select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option value="NOTES">Notes</option><option value="PREVIOUS_PAPER">Previous paper</option><option value="MODEL_PAPER">Model paper</option><option value="INTERNAL_PAPER">Internal paper</option><option value="ASSIGNMENT">Assignment</option><option value="LAB_MANUAL">Lab manual</option><option value="PRACTICAL">Practical record</option><option value="SYLLABUS">Syllabus</option><option value="IMPORTANT_QUESTIONS">Important questions</option><option value="REFERENCE">Reference material</option></select></Field>
          <Field label="Semester"><select required value={form.semester} onChange={(event) => {
            const semester = semesters.find((item) => item.id === Number(event.target.value))
            setForm({ ...form, semester: event.target.value, academic_year: semester?.academic_year || '', subject: '', module: '' })
          }}><option value="">Choose semester</option>{semesters.map((item) => <option key={item.id} value={item.id}>Semester {item.semester_number} · {item.academic_year}</option>)}</select></Field>
          <Field label="Subject"><select required value={form.subject} onChange={(event) => setForm({ ...form, subject: event.target.value })}><option value="">Choose subject</option>{subjects.filter((item) => !form.semester || item.semester === Number(form.semester)).map((item) => <option key={item.id} value={item.id}>{item.subject_code} · {item.subject_name}</option>)}</select></Field>
          <Field label="Module (optional)"><input type="number" min={1} value={form.module} onChange={(event) => setForm({ ...form, module: event.target.value })}/></Field>
          <Field label="Academic year"><input required readOnly value={form.academic_year} placeholder="Select a semester"/></Field>
          <Field label="Description"><input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })}/></Field>
          <label className="file-input"><input type="file" accept=".pdf,.docx,.pptx" onChange={(event) => setFile(event.target.files?.[0] || null)}/><Upload size={19}/><span>{file?.name || 'Choose PDF, DOCX or PPTX · 25 MB max'}</span></label>
        </div>
        <p className="form-hint">HOD uploads are immediately published as approved department resources.</p>
        {error && <ErrorNotice>{error}</ErrorNotice>}
        <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? 'Uploading…' : 'Upload material'}</button></div>
      </form>
    </section>
  </div>
}

export function HodMaterialsContent({ initialStatus = '' }: { initialStatus?: string }) {
  const [materials, setMaterials] = useState<Material[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [statusFilter, setStatusFilter] = useState(initialStatus)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = useCallback(async () => {
    try {
      const [materialsResponse, subjectsResponse, semestersResponse] = await Promise.all([
        api.get<Collection<Material>>('/hod/materials/', { params: { approval_status: statusFilter || undefined } }),
        api.get<Collection<Subject>>('/hod/subjects/'),
        api.get<Collection<Semester>>('/hod/semesters/'),
      ])
      setError('')
      setMaterials(collection(materialsResponse.data))
      setSubjects(collection(subjectsResponse.data))
      setSemesters(collection(semestersResponse.data))
    } catch (reason) {
      setError(errorText(reason))
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => { void load() }, [load])

  const review = async (material: Material, action: 'approve' | 'reject') => {
    const rejection_reason = action === 'reject'
      ? window.prompt(`Why are you rejecting “${material.title}”?`)?.trim() || ''
      : ''
    if (action === 'reject' && !rejection_reason) return
    setError('')
    try {
      await api.post(`/hod/materials/${material.id}/${action}/`, { rejection_reason })
      setNotice(action === 'approve' ? 'Material approved.' : 'Material rejected.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const download = async (material: Material) => {
    try {
      const response = await api.get(`/hod/materials/${material.id}/download/`, { responseType: 'blob' })
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = `${material.title.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '')}`
      link.click()
      URL.revokeObjectURL(url)
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const archive = async (material: Material) => {
    if (!window.confirm(`Archive “${material.title}”? It will no longer be publicly visible.`)) return
    try {
      await api.delete(`/hod/materials/${material.id}/`)
      setNotice('Material archived.')
      await load()
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  const upload = async () => {
    setUploadOpen(false)
    setNotice('Material uploaded and published.')
    await load()
  }

  return <>
    <section className="panel">
      <div className="admin-toolbar">
        <select aria-label="Filter material status" value={statusFilter} onChange={(event) => { setLoading(true); setStatusFilter(event.target.value) }}><option value="">All statuses</option><option value="PENDING">Pending approval</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option><option value="ARCHIVED">Archived</option></select>
        <button className="button primary" onClick={() => setUploadOpen(true)}><Upload size={16}/> Upload material</button>
      </div>
      {notice && <div className="success-message" role="status">{notice}</div>}
      {error && <ErrorNotice>{error}</ErrorNotice>}
      {loading ? <p className="muted-copy">Loading department materials…</p> : materials.length ? <div className="table-wrap"><table><thead><tr><th>Material</th><th>Subject / semester</th><th>Uploaded by</th><th>Downloads</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>{materials.map((material) => <tr key={material.id}>
          <td><strong>{material.title}</strong><small className="table-subtext">{material.category.replaceAll('_', ' ').toLowerCase()}</small></td>
          <td>{material.subject_code || material.subject_name} · Sem {semesters.find((item) => item.id === material.semester)?.semester_number || '—'}</td>
          <td>{material.uploaded_by_name}</td><td>{material.download_count}</td>
          <td><span className={`status ${material.approval_status.toLowerCase()}`}>{material.approval_status}</span></td>
          <td><div className="teacher-actions">
            <button className="button secondary compact" onClick={() => void download(material)} aria-label={`Download ${material.title}`}><Download size={14}/></button>
            {material.approval_status === 'PENDING' && <>
              <button className="button primary compact" onClick={() => void review(material, 'approve')}><Check size={14}/> Approve</button>
              <button className="button danger compact" onClick={() => void review(material, 'reject')}>Reject</button>
            </>}
            {material.approval_status !== 'ARCHIVED' && <button className="button secondary compact" onClick={() => void archive(material)} aria-label={`Archive ${material.title}`}><Archive size={14}/></button>}
          </div></td>
        </tr>)}</tbody></table></div> : <EmptyNotice title="No materials found" text="Approved public resources and pending reviews appear here."/>}
    </section>
    {uploadOpen && <MaterialUpload semesters={semesters} subjects={subjects} onClose={() => setUploadOpen(false)} onUploaded={upload}/>}
  </>
}

export function HodReportsContent() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<DashboardData>('/hod/dashboard/'),
      api.get<Collection<Activity>>('/hod/audit/'),
    ]).then(([dashboard, audit]) => {
      setData(dashboard.data)
      setActivities(collection(audit.data))
    }).catch((reason: unknown) => setError(errorText(reason))).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="muted-copy">Loading department report…</p>
  if (error || !data) return <ErrorNotice>{error || 'Department report is unavailable.'}</ErrorNotice>

  return <>
    <div className="stat-grid four">
      <Stat label="Students" value={data.students} detail="Department enrollment" tone="blue"/>
      <Stat label="Teachers" value={data.teachers} detail="Active and inactive records" tone="green"/>
      <Stat label="Subjects" value={data.subjects} detail={`${data.assigned_subjects} subject assignments`} tone="amber"/>
      <Stat label="Materials" value={data.materials} detail={`${data.approved_materials} approved`} tone="red"/>
    </div>
    <section className="panel"><PanelHeading title="Department audit trail"/>
      {activities.length ? <div className="audit-list">{activities.map((activity) => <article key={activity.id}>
        <span className="audit-dot"/><div><strong>{formatAction(activity.action)}</strong><p>{activity.actor}{activity.target ? ` · ${activity.target}` : ''}</p><small>{new Date(activity.created_at).toLocaleString()}</small></div>
      </article>)}</div> : <EmptyNotice title="No audit events" text="Administrative changes will be recorded here."/>}
    </section>
    <section className="panel"><PanelHeading title="Study material totals"/>
      <div className="coverage-list">
        <Coverage label="Approved" value={data.approved_materials} max={data.materials}/>
        <Coverage label="Pending approval" value={data.pending_materials} max={data.materials}/>
        <Coverage label="Total department materials" value={data.materials} max={data.materials}/>
      </div>
    </section>
  </>
}

function Coverage({ label, value, max }: { label: string; value: number; max: number }) {
  return <div className="coverage"><div><span>{label}</span><strong>{value}</strong></div><div className="status-bar"><span style={{ width: `${max ? Math.min(100, value / max * 100) : 0}%` }}/></div></div>
}

export function HodSettingsContent() {
  const [account, setAccount] = useState<Account | null>(null)
  const [form, setForm] = useState({ first_name: '', last_name: '' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Account>('/hod/account/')
      .then((response) => {
        setAccount(response.data)
        setForm({ first_name: response.data.first_name, last_name: response.data.last_name })
      })
      .catch((reason: unknown) => setError(errorText(reason)))
      .finally(() => setLoading(false))
  }, [])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      const response = await api.patch<Account>('/hod/account/', form)
      setAccount(response.data)
      setNotice('Account details updated.')
    } catch (reason) {
      setError(errorText(reason))
    }
  }

  if (loading) return <p className="muted-copy">Loading account settings…</p>
  if (!account) return <ErrorNotice>{error || 'Account settings are unavailable.'}</ErrorNotice>

  return <div className="dashboard-grid hod-grid">
    <section className="panel">
      <PanelHeading title="Department HOD account"/>
      <form className="form-grid" onSubmit={submit}>
        <Field label="First name"><input required value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })}/></Field>
        <Field label="Last name"><input required value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })}/></Field>
        <Field label="Official email"><input readOnly value={account.email}/></Field>
        <Field label="Department"><input readOnly value={`${account.department_name} (${account.department_code})`}/></Field>
        {error && <ErrorNotice>{error}</ErrorNotice>}{notice && <div className="success-message">{notice}</div>}
        <div className="form-actions"><button className="button primary">Save account details</button></div>
      </form>
    </section>
    <section className="panel account-security">
      <div className="security-icon"><ShieldCheck size={22}/></div>
      <h2>Account security</h2>
      <p>Update your password regularly. Password resets are sent only to your official department email.</p>
      <a className="button secondary" href="/change-password">Change password <ArrowRight size={15}/></a>
      <a className="security-link" href="/password-reset">Forgot your password?</a>
    </section>
  </div>
}
