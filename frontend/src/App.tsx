import { useEffect, useState } from 'react'
import type { CSSProperties, FormEvent, ReactNode } from 'react'
import { motion } from 'framer-motion'
import { GlassStatCard, pageMotion } from './components/GlassComponents'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import axios from 'axios'
import aiemsCampus from './assets/aiems-campus.png'
import {
  ArrowRight, Bell, Bookmark, BookOpen, Building2, ChevronLeft,
  ChevronRight, CircleUserRound, Download, FileText, GraduationCap,
  LayoutDashboard, Library, LogOut, Menu, Moon, MoreHorizontal, Search,
  Settings, Sun, Upload, Users, X,
} from 'lucide-react'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
})

type Session = {
  access: string
  refresh: string
  user: { id: number; name: string; email: string; role: 'HOD' | 'TEACHER' | 'STUDENT' }
}
type Material = {
  id: number
  title: string
  description?: string
  category: string
  approval_status: string
  subject_name?: string
  subject_code?: string
  uploaded_by_name?: string
  uploaded_at: string
  download_count: number
  file?: string
  module?: number
}

function getSession(): Session | null {
  try { return JSON.parse(localStorage.getItem('aiems_session') || 'null') } catch { return null }
}

function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand">
      <div className="brand-mark"><GraduationCap size={compact ? 18 : 21} strokeWidth={2.2}/></div>
      <div className="brand-copy"><strong>AIEMS</strong>{!compact && <span>Learning Hub</span>}</div>
    </div>
  )
}

function PublicHeader() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [dark, setDark] = useState(localStorage.getItem('theme') === 'dark')
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])
  return (
    <header className="public-header">
      <a href="/" aria-label="AIEMS Hub home"><Logo/></a>
      <nav className={menuOpen ? 'public-nav open' : 'public-nav'}>
        <a href="/">Home</a><a href="/#departments">Departments</a><a href="/#resources">Resources</a><a href="/#about">About</a><a href="#contact">Contact</a>
      </nav>
      <div className="public-actions">
        <button className="icon-button" onClick={() => setDark(!dark)} aria-label="Toggle theme">{dark ? <Sun size={17}/> : <Moon size={17}/>}</button>
        <a className="button primary compact" href="/login">Faculty login</a>
      </div>
      <button className="mobile-nav-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">{menuOpen ? <X/> : <Menu/>}</button>
    </header>
  )
}

function Home() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const departments = [
    ['AIML','Artificial Intelligence & ML'], ['CSE','Computer Science'], ['ISE','Information Science'],
    ['ECE','Electronics & Communication'], ['EEE','Electrical & Electronics'], ['ME','Mechanical'], ['CE','Civil'],
  ]
  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    navigate(query ? `/materials?q=${encodeURIComponent(query)}` : '/materials')
  }
  return (
    <motion.div className="public-site" {...pageMotion}>
      <PublicHeader/>
      <main>
        <section
          className="hero-section campus-hero"
          style={{ '--campus-image': `url(${aiemsCampus})` } as CSSProperties}
        >
          <div className="hero-content">
            <div className="eyebrow"><span></span> AIEMS Academic Hub</div>
            <h1>Your Academic World, All in One Place.</h1>
            <p>Notes, question papers, assignments and reference material for every semester—verified by your faculty and available in one place.</p>
            <form className="search-hero" onSubmit={submitSearch}>
              <Search size={20}/>
              <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by subject, module or resource"/>
              <button type="submit">Search <ArrowRight size={16}/></button>
            </form>
            <div className="hero-links">
              <a className="button primary" href="/materials">Explore resources <ChevronRight size={17}/></a>
              <a className="text-link" href="/login">HOD / Teacher login <ArrowRight size={16}/></a>
            </div>
          </div>
          <div className="hero-study-card" aria-label="Resource overview">
            <div className="study-card-top">
              <div><span>Study workspace</span><strong>Semester 5</strong></div>
              <div className="avatar-stack"><b>AI</b><b>CS</b><b>+3</b></div>
            </div>
            <div className="progress-line"><span></span></div>
            <div className="study-row"><div className="file-icon blue"><FileText size={18}/></div><div><strong>Database Management</strong><span>Module 4 · Notes</span></div><small>PDF</small></div>
            <div className="study-row"><div className="file-icon amber"><BookOpen size={18}/></div><div><strong>Computer Networks</strong><span>Previous year papers</span></div><small>PDF</small></div>
            <div className="study-row"><div className="file-icon green"><Library size={18}/></div><div><strong>Operating Systems</strong><span>Reference material</span></div><small>DOCX</small></div>
          </div>
        </section>

        <section className="semester-strip" aria-label="Browse by semester">
          <span>Browse by semester</span>
          <div>{[1,2,3,4,5,6,7,8].map(n => <button key={n}>Semester {n}</button>)}</div>
        </section>

        <section className="public-section" id="departments">
          <SectionHeading overline="Departments" title="Choose your department" action="View all departments"/>
          <div className="department-grid">
            {departments.map(([code,name]) => (
              <a className="department-card" href="/login" key={code}>
                <div className="department-code">{code}</div>
                <div><h3>{name}</h3><p>View resources <ArrowRight size={14}/></p></div>
              </a>
            ))}
          </div>
        </section>

        <section className="public-section resources-section" id="resources">
          <SectionHeading overline="Resource library" title="Learning resources, made accessible"/>
          <div className="feature-grid">
            <Feature icon={<FileText/>} title="Module-wise notes" text="Structured study material from Module 1 through Module 5."/>
            <Feature icon={<BookOpen/>} title="Question papers" text="Previous year, model and internal assessment papers."/>
            <Feature icon={<Library/>} title="Academic references" text="Assignments, lab manuals, syllabi and practical records."/>
          </div>
        </section>

        <section className="public-section about-section" id="about">
          <div className="about-copy"><span className="overline">About AIEMS</span><h2>Built around the way your college learns.</h2><p>A focused academic workspace that keeps faculty contributions and student access clear, organized and secure.</p></div>
          <div className="about-metrics"><Metric value="3" label="Access roles"/><Metric value="8" label="Semesters"/><Metric value="5" label="Learning modules"/></div>
        </section>
      </main>
      <footer className="public-footer" id="contact"><a href="/"><Logo/></a><p>AIEMS College · Your College. Your Learning. Your Future.</p><div><a href="/login">Faculty login</a></div></footer>
    </motion.div>
  )
}

function SectionHeading({overline,title,action}:{overline:string,title:string,action?:string}) {
  return <div className="section-heading"><div><span>{overline}</span><h2>{title}</h2></div>{action && <a href="/login">{action} <ArrowRight size={15}/></a>}</div>
}
function Feature({icon,title,text}:{icon:ReactNode,title:string,text:string}) {
  return <article className="feature-card"><div className="feature-icon">{icon}</div><h3>{title}</h3><p>{text}</p></article>
}
function Metric({value,label}:{value:string,label:string}) {
  return <div className="metric"><strong>{value}</strong><span>{label}</span></div>
}

function AuthPage({register=false}:{register?:boolean}) {
  const navigate = useNavigate()
  const [loading,setLoading] = useState(false)
  const [error,setError] = useState('')
  const [form,setForm] = useState<any>({
    username:'',password:'',password_confirm:'',first_name:'',last_name:'',
    email:'',usn:'',department:'',semester:'',academic_year:'',
  })
  const submit = async (event:FormEvent) => {
    event.preventDefault(); setLoading(true); setError('')
    try {
      if (register) await api.post('/auth/register/student/',form)
      const res = await api.post('/auth/login/',{username:form.username,password:form.password})
      localStorage.setItem('aiems_session',JSON.stringify(res.data))
      api.defaults.headers.common.Authorization = `Bearer ${res.data.access}`
      navigate(res.data.user.role === 'HOD' ? '/hod' : res.data.user.role === 'TEACHER' ? '/teacher' : '/student')
    } catch (err:any) {
      const data=err?.response?.data
      setError(typeof data === 'string' ? data : data?.detail || data?.password_confirm?.[0] || 'Unable to continue.')
    } finally { setLoading(false) }
  }
  return (
    <div className="auth-layout">
      <div className="auth-aside">
        <a href="/"><Logo/></a>
        <div><span className="overline">AIEMS Learning Hub</span><h1>{register ? 'Start your academic journey.' : 'Faculty workspace access.'}</h1><p>{register ? 'Create your student workspace and access approved college resources.' : 'Manage academic resources and administrative responsibilities.'}</p></div>
        <div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div>
      </div>
      <div className="auth-panel">
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-heading"><span>{register ? 'Create account' : 'Faculty access'}</span><h2>{register ? 'Student registration' : 'HOD / Teacher sign in'}</h2></div>
          {register && <div className="form-grid">
            <Field label="First name"><input required value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})}/></Field>
            <Field label="Last name"><input value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})}/></Field>
            <Field label="Email"><input type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></Field>
            <Field label="USN"><input required value={form.usn} onChange={e=>setForm({...form,usn:e.target.value})}/></Field>
            <Field label="Department ID"><input required value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/></Field>
            <Field label="Semester ID"><input required value={form.semester} onChange={e=>setForm({...form,semester:e.target.value})}/></Field>
            <Field label="Academic year" span><input required placeholder="2025-2026" value={form.academic_year} onChange={e=>setForm({...form,academic_year:e.target.value})}/></Field>
          </div>}
          <Field label="Username"><input required value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></Field>
          <Field label="Password"><input type="password" required value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></Field>
          {register && <Field label="Confirm password"><input type="password" required value={form.password_confirm} onChange={e=>setForm({...form,password_confirm:e.target.value})}/></Field>}
          {error && <div className="error-message">{error}</div>}
          <button className="button primary full" disabled={loading}>{loading ? 'Please wait…' : register ? 'Create account' : 'Sign in'} {!loading && <ArrowRight size={17}/>}</button>
          {register && <p className="auth-switch">Already have an account? <a href="/login">Sign in</a></p>}
        </form>
      </div>
    </div>
  )
}
function Field({label,children,span=false}:{label:string,children:ReactNode,span?:boolean}) {
  return <label className={span ? 'field span' : 'field'}><span>{label}</span>{children}</label>
}

function Sidebar({role,collapsed,onCollapse}:{role:Session['user']['role'],collapsed:boolean,onCollapse:()=>void}) {
  const navigate=useNavigate()
  const session=getSession()
  const items = role==='HOD'
    ? [['/hod','Overview',LayoutDashboard],['/hod/teachers','Teachers',Users],['/hod/materials','Approvals',Library],['/hod/academics','Academics',Building2],['/hod/reports','Reports',Settings]]
    : role==='TEACHER'
    ? [['/teacher','Overview',LayoutDashboard],['/teacher/upload','Upload',Upload],['/teacher/materials','My uploads',Library],['/teacher/subjects','Assigned subjects',BookOpen]]
    : [['/student','Overview',LayoutDashboard],['/materials','Library',Library],['/student/bookmarks','Bookmarks',Bookmark],['/student/profile','Profile',CircleUserRound]]
  const logout=()=>{localStorage.removeItem('aiems_session');navigate('/')}
  return (
    <aside className={collapsed?'sidebar collapsed':'sidebar'}>
      <div className="sidebar-brand"><a href="/"><Logo compact={collapsed}/></a><button onClick={onCollapse} aria-label="Collapse sidebar"><ChevronLeft size={16}/></button></div>
      <nav>{items.map(([path,label,Icon])=>{
        const IconComponent=Icon as typeof LayoutDashboard
        return <a href={String(path)} key={String(path)} className={location.pathname===String(path)?'active':''}><IconComponent size={18}/><span>{String(label)}</span></a>
      })}</nav>
      <div className="sidebar-user"><div className="user-avatar">{session?.user.name.slice(0,1).toUpperCase()}</div><div><strong>{session?.user.name}</strong><span>{role.toLowerCase()}</span></div><button onClick={logout} aria-label="Log out"><LogOut size={17}/></button></div>
    </aside>
  )
}

function Dashboard({role,children,title,subtitle}:{role:Session['user']['role'],children:ReactNode,title:string,subtitle:string}) {
  const [collapsed,setCollapsed]=useState(false)
  const [mobileOpen,setMobileOpen]=useState(false)
  const [dark,setDark]=useState(localStorage.getItem('theme')==='dark')
  useEffect(()=>{
    document.documentElement.dataset.theme=dark?'dark':'light'
    localStorage.setItem('theme',dark?'dark':'light')
  },[dark])
  return (
    <div className={collapsed?'dashboard-shell collapsed':'dashboard-shell'}>
      <div className={mobileOpen?'sidebar-mobile open':'sidebar-mobile'} onClick={()=>setMobileOpen(false)}></div>
      <Sidebar role={role} collapsed={collapsed} onCollapse={()=>setCollapsed(!collapsed)}/>
      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <button className="mobile-menu-button" onClick={()=>setMobileOpen(true)}><Menu size={20}/></button>
          <div><span>AIEMS Hub</span><ChevronRight size={13}/><strong>{title}</strong></div>
          <div className="topbar-actions"><button className="icon-button" onClick={()=>setDark(!dark)} aria-label="Toggle theme">{dark?<Sun size={17}/>:<Moon size={17}/>}</button><button className="icon-button notification" aria-label="Notifications"><Bell size={17}/><i></i></button></div>
        </header>
        <div className="dashboard-content"><div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div></div>{children}</div>
      </main>
    </div>
  )
}

function StatCard({label,value,detail,icon,tone='blue'}:{label:string,value:string|number,detail:string,icon:ReactNode,tone?:string}) {
  const normalizedTone = tone === 'green' || tone === 'amber' || tone === 'red' ? tone : 'blue'
  return <GlassStatCard label={label} value={value} detail={detail} icon={icon} tone={normalizedTone}/>
}

function EmptyState({title,text}:{title:string,text:string}) {
  return <div className="empty-state"><div><FileText size={22}/></div><h3>{title}</h3><p>{text}</p></div>
}

function StudentDashboard() {
  const [data,setData]=useState<any>(null)
  const [loading,setLoading]=useState(true)
  useEffect(()=>{
    const session=getSession(); if(!session)return
    api.defaults.headers.common.Authorization=`Bearer ${session.access}`
    api.get('/student/dashboard/').then(r=>setData(r.data)).finally(()=>setLoading(false))
  },[])
  const recent=data?.recent_materials||[]
  const popular=data?.popular_materials||[]
  return <Dashboard role="STUDENT" title="Overview" subtitle="Your academic workspace">
    {loading ? <div className="stat-grid">{[1,2,3].map(n=><div className="stat-card skeleton" key={n}></div>)}</div> :
    <>
      <section className="welcome-banner"><div><span>Welcome back</span><h2>Continue learning with your semester resources.</h2><p>{data?.department} · Semester {data?.semester}</p></div><a className="button white" href="/materials">Browse library <ArrowRight size={16}/></a></section>
      <div className="stat-grid student-stats">
        <StatCard label="Department" value={data?.department||'—'} detail="Your academic department" icon={<Building2/>} tone="blue"/>
        <StatCard label="Current semester" value={data?.semester||'—'} detail="Active academic period" icon={<GraduationCap/>} tone="amber"/>
        <StatCard label="Available subjects" value={data?.subjects?.length||0} detail="For this semester" icon={<BookOpen/>} tone="green"/>
      </div>
      <div className="dashboard-grid">
        <section className="panel subjects-panel"><PanelHeading title="Your subjects" action="View all" href="/student"/><div className="subject-grid">
          {(data?.subjects||[]).slice(0,6).map((subject:any)=><a className="subject-card" href="/materials" key={subject.id}><div className="subject-code">{subject.subject_code}</div><div><h3>{subject.subject_name}</h3><p>View resources <ArrowRight size={13}/></p></div></a>)}
          {!data?.subjects?.length && <EmptyState title="No subjects assigned" text="Subjects configured for your semester will appear here."/>}
        </div></section>
        <section className="panel activity-panel"><PanelHeading title="Quick access"/><a href="/materials"><div className="quick-icon"><Library/></div><div><strong>Resource library</strong><span>Search approved materials</span></div><ChevronRight/></a><a href="/student/bookmarks"><div className="quick-icon amber"><Bookmark/></div><div><strong>Bookmarks</strong><span>Open saved resources</span></div><ChevronRight/></a></section>
      </div>
      <section className="panel"><PanelHeading title="Recently uploaded" action="View library" href="/materials"/><MaterialList materials={recent}/></section>
      <section className="panel"><PanelHeading title="Popular resources" action="View library" href="/materials"/><MaterialList materials={popular}/></section>
    </>}
  </Dashboard>
}

function PanelHeading({title,action,href}:{title:string,action?:string,href?:string}) {
  return <div className="panel-heading"><h2>{title}</h2>{action&&<a href={href}>{action} <ArrowRight size={14}/></a>}</div>
}

async function downloadMaterial(material: Material) {
  const session = getSession()
  if (!session) return
  const response = await api.get(`/student/materials/${material.id}/download/`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = material.title.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') + '.pdf'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

async function bookmarkMaterial(material: Material) {
  await api.post('/student/bookmarks/', { material: material.id })
}

function MaterialList({materials}:{materials:Material[]}) {
  if(!materials?.length) return <EmptyState title="No approved materials yet" text="Approved academic resources will appear here."/>
  return <div className="material-list">{materials.map(material=><article className="material-row" key={material.id}><div className="file-icon blue"><FileText size={18}/></div><div className="material-info"><strong>{material.title}</strong><span>{material.subject_name||'Academic resource'} · {material.category.replaceAll('_',' ').toLowerCase()}</span></div><div className="material-meta"><span>{material.approval_status}</span><small>{material.download_count||0} downloads</small></div><button className="icon-button" title="Bookmark" onClick={()=>bookmarkMaterial(material)}><Bookmark size={16}/></button><button className="icon-button" title="Download" onClick={()=>downloadMaterial(material)}><Download size={16}/></button></article>)}</div>
}

function TeacherDashboard() {
  const [materials,setMaterials]=useState<Material[]>([])
  const [loading,setLoading]=useState(true)
  const [showUpload,setShowUpload]=useState(false)
  useEffect(()=>{
    const session=getSession(); if(!session)return
    api.defaults.headers.common.Authorization=`Bearer ${session.access}`
    api.get('/teacher/materials/').then(r=>setMaterials(Array.isArray(r.data)?r.data:r.data.results||[])).finally(()=>setLoading(false))
  },[])
  const approved=materials.filter(m=>m.approval_status==='APPROVED').length
  const pending=materials.filter(m=>m.approval_status==='PENDING').length
  const rejected=materials.filter(m=>m.approval_status==='REJECTED').length
  return <Dashboard role="TEACHER" title="Overview" subtitle="Manage your academic contributions">
    <div className="stat-grid">
      <StatCard label="Total uploads" value={materials.length} detail="All submitted resources" icon={<Upload/>} tone="blue"/>
      <StatCard label="Approved" value={approved} detail="Visible to students" icon={<FileText/>} tone="green"/>
      <StatCard label="Pending review" value={pending} detail="Awaiting HOD approval" icon={<Bell/>} tone="amber"/>
      <StatCard label="Needs revision" value={rejected} detail="Rejected submissions" icon={<X/>} tone="red"/>
    </div>
    <div className="dashboard-grid teacher-grid">
      <section className="panel"><PanelHeading title="Recent uploads" action="View all"/>{loading?<EmptyState title="Loading uploads" text="Fetching your latest submissions."/>:<MaterialTable materials={materials.slice(0,8)}/>}</section>
      <section className="panel"><PanelHeading title="Quick upload"/><button className="upload-dropzone" onClick={()=>setShowUpload(true)}><div><Upload size={22}/></div><strong>Add study material</strong><span>PDF, DOCX or PPTX · 25 MB max</span></button><div className="approval-summary"><div><span>Approval status</span><strong>{pending} pending</strong></div><div className="status-bar"><span style={{width:`${materials.length?approved/materials.length*100:0}%`}}></span></div></div></section>
    </div>
    {showUpload&&<UploadModal onClose={()=>setShowUpload(false)} onUploaded={()=>window.location.reload()}/>}
  </Dashboard>
}

function UploadModal({onClose,onUploaded}:{onClose:()=>void,onUploaded:()=>void}) {
  const [form,setForm]=useState<any>({title:'',description:'',department:'',semester:'',subject:'',module:'',category:'NOTES',academic_year:''})
  const [file,setFile]=useState<File|null>(null)
  const [progress,setProgress]=useState(0)
  const [error,setError]=useState('')
  const submit=async(e:FormEvent)=>{
    e.preventDefault(); setError('')
    if(!file){setError('Choose a document to upload.');return}
    const data=new FormData()
    Object.entries(form).forEach(([key,value])=>{if(value!==''&&value!=null)data.append(key,String(value))})
    data.append('file',file)
    try{
      await api.post('/teacher/materials/',data,{headers:{'Content-Type':'multipart/form-data'},onUploadProgress:p=>setProgress(Math.round((p.loaded/(p.total||1))*100))})
      onUploaded()
    }catch(err:any){setError(err?.response?.data?.detail||'Upload failed. Check subject assignment and required fields.')}
  }
  return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal" onMouseDown={e=>e.stopPropagation()}><div className="modal-heading"><div><span>Study material</span><h2>Upload resource</h2></div><button className="icon-button" onClick={onClose}><X size={17}/></button></div><form onSubmit={submit}><div className="form-grid"><Field label="Material title" span><input required value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/></Field><Field label="Department ID"><input required value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/></Field><Field label="Semester ID"><input required value={form.semester} onChange={e=>setForm({...form,semester:e.target.value})}/></Field><Field label="Subject ID"><input required value={form.subject} onChange={e=>setForm({...form,subject:e.target.value})}/></Field><Field label="Module"><input value={form.module} onChange={e=>setForm({...form,module:e.target.value})}/></Field><Field label="Category"><select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}><option value="NOTES">Subject notes</option><option value="PREVIOUS_PAPER">Previous paper</option><option value="MODEL_PAPER">Model paper</option><option value="ASSIGNMENT">Assignment</option><option value="LAB_MANUAL">Lab manual</option><option value="SYLLABUS">Syllabus</option><option value="REFERENCE">Reference material</option></select></Field><Field label="Academic year"><input required placeholder="2025-2026" value={form.academic_year} onChange={e=>setForm({...form,academic_year:e.target.value})}/></Field><Field label="Description" span><textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></Field><label className="file-input span"><input type="file" accept=".pdf,.docx,.pptx" onChange={e=>setFile(e.target.files?.[0]||null)}/><Upload size={20}/><span>{file?file.name:'Choose PDF, DOCX or PPTX'}</span></label></div>{progress>0&&<div className="upload-progress"><span style={{width:`${progress}%`}}></span></div>}{error&&<div className="error-message">{error}</div>}<div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={progress>0&&progress<100}>Upload material</button></div></form></div></div>
}

function MaterialTable({materials}:{materials:Material[]}) {
  if(!materials.length)return <EmptyState title="No uploads yet" text="Use the upload action to submit your first resource."/>
  return <div className="table-wrap"><table><thead><tr><th>Resource</th><th>Type</th><th>Status</th><th>Downloads</th><th></th></tr></thead><tbody>{materials.map(m=><tr key={m.id}><td><div className="table-resource"><div className="file-icon blue"><FileText size={17}/></div><div><strong>{m.title}</strong><span>{m.subject_name||m.subject_code||'Academic resource'}</span></div></div></td><td>{m.category.replaceAll('_',' ').toLowerCase()}</td><td><Status status={m.approval_status}/></td><td>{m.download_count||0}</td><td><button className="icon-button"><MoreHorizontal size={16}/></button></td></tr>)}</tbody></table></div>
}
function Status({status}:{status:string}) {
  return <span className={`status ${status.toLowerCase()}`}>{status==='PENDING'?'Pending review':status==='APPROVED'?'Approved':status==='REJECTED'?'Needs revision':status}</span>
}

async function reviewMaterial(material: Material, action: 'approve' | 'reject') {
  let rejectionReason = ''
  if (action === 'reject') {
    rejectionReason = window.prompt('Reason for rejecting this material')?.trim() || ''
    if (!rejectionReason) return
  }
  await api.post(`/hod/materials/${material.id}/${action}/`, {
    rejection_reason: rejectionReason,
  })
  window.location.reload()
}

function HodDashboard() {
  const [data,setData]=useState<any>(null)
  const [teachers,setTeachers]=useState<any[]>([])
  const [materials,setMaterials]=useState<Material[]>([])
  const [loading,setLoading]=useState(true)
  useEffect(()=>{
    const session=getSession();if(!session)return
    api.defaults.headers.common.Authorization=`Bearer ${session.access}`
    Promise.all([api.get('/hod/dashboard/'),api.get('/hod/teachers/'),api.get('/hod/materials/')])
      .then(([d,t,m])=>{setData(d.data);setTeachers(Array.isArray(t.data)?t.data:t.data.results||[]);setMaterials(Array.isArray(m.data)?m.data:m.data.results||[])})
      .finally(()=>setLoading(false))
  },[])
  const pending=materials.filter(m=>m.approval_status==='PENDING')
  return <Dashboard role="HOD" title="Administration" subtitle="Monitor academics and material approvals">
    {loading?<div className="stat-grid">{[1,2,3,4].map(n=><div className="stat-card skeleton" key={n}></div>)}</div>:<>
      <div className="stat-grid four">
        <StatCard label="Students" value={data?.students||0} detail="Registered learners" icon={<Users/>} tone="blue"/>
        <StatCard label="Teachers" value={data?.teachers||0} detail="Faculty accounts" icon={<CircleUserRound/>} tone="green"/>
        <StatCard label="Departments" value={data?.departments||0} detail="Academic departments" icon={<Building2/>} tone="amber"/>
        <StatCard label="Pending approvals" value={data?.pending_materials||0} detail="Requires review" icon={<Library/>} tone="red"/>
      </div>
      <div className="dashboard-grid hod-grid">
        <section className="panel"><PanelHeading title="Pending material approvals" action={`${pending.length} waiting`}/>{pending.length?<div className="approval-list">{pending.slice(0,5).map(m=><div className="approval-row" key={m.id}><div className="file-icon amber"><FileText size={17}/></div><div><strong>{m.title}</strong><span>{m.subject_name||'Academic resource'} · {m.uploaded_by_name||'Teacher'}</span></div><div className="approval-actions"><button className="glass-button approve" onClick={()=>reviewMaterial(m,'approve')}>Approve</button><button className="glass-button reject" onClick={()=>reviewMaterial(m,'reject')}>Reject</button></div></div>)}</div>:<EmptyState title="All caught up" text="There are no materials waiting for review."/>}</section>
        <section className="panel"><PanelHeading title="Academic coverage"/><div className="coverage-list"><Coverage label="Subjects" value={data?.subjects||0} max={data?.subjects||1}/><Coverage label="Approved" value={data?.approved_materials||0} max={data?.materials||1}/><Coverage label="Pending" value={data?.pending_materials||0} max={data?.materials||1}/></div></section>
      </div>
      <section className="panel"><PanelHeading title="Teacher directory" action="Manage teachers"/><div className="table-wrap"><table><thead><tr><th>Teacher</th><th>Email</th><th>Employee ID</th><th>Department</th><th>Status</th></tr></thead><tbody>{teachers.map((teacher:any)=><tr key={teacher.id}><td><div className="table-resource"><div className="user-avatar small">{(teacher.first_name||teacher.username).slice(0,1).toUpperCase()}</div><strong>{teacher.first_name||teacher.username} {teacher.last_name||''}</strong></div></td><td>{teacher.email||'—'}</td><td>{teacher.teacher_profile?.employee_id||'—'}</td><td>{teacher.teacher_profile?.department_name||'—'}</td><td><span className={teacher.is_active?'status approved':'status rejected'}>{teacher.is_active?'Active':'Inactive'}</span></td></tr>)}</tbody></table></div>{!teachers.length&&<EmptyState title="No teachers yet" text="Teacher accounts created by the HOD will appear here."/>}</section>
    </>}
  </Dashboard>
}
function Coverage({label,value,max}:{label:string,value:number,max:number}) {
  return <div className="coverage"><div><span>{label}</span><strong>{value}</strong></div><div className="status-bar"><span style={{width:`${max?Math.min(100,value/max*100):0}%`}}></span></div></div>
}

function MaterialsLibrary() {
  const [materials,setMaterials]=useState<Material[]>([])
  const [query,setQuery]=useState('')
  const [category,setCategory]=useState('')
  const [loading,setLoading]=useState(true)
  useEffect(()=>{
    const session=getSession()
    if(session)api.defaults.headers.common.Authorization=`Bearer ${session.access}`
    api.get('/student/materials/',{params:{search:query||undefined,category:category||undefined}})
      .then(r=>setMaterials(Array.isArray(r.data)?r.data:r.data.results||[])).finally(()=>setLoading(false))
  },[query,category])
  const session=getSession()
  return session?<Dashboard role={session.user.role} title="Resource library" subtitle="Search and filter approved academic materials">
    <section className="library-toolbar"><div className="library-search"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search title, subject or subject code"/></div><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option><option value="NOTES">Notes</option><option value="PREVIOUS_PAPER">Previous papers</option><option value="MODEL_PAPER">Model papers</option><option value="ASSIGNMENT">Assignments</option><option value="LAB_MANUAL">Lab manuals</option><option value="SYLLABUS">Syllabus</option></select></section>
    {loading?<div className="material-card-grid">{[1,2,3,4].map(n=><div className="material-card skeleton" key={n}></div>)}</div>:materials.length?<div className="material-card-grid">{materials.map(m=><article className="material-card" key={m.id}><div className="material-card-top"><div className="file-icon blue"><FileText/></div><button className="icon-button" title="Bookmark" onClick={()=>bookmarkMaterial(m)}><Bookmark size={16}/></button></div><span className="category-label">{m.category.replaceAll('_',' ').toLowerCase()}</span><h3>{m.title}</h3><p>{m.description||'Approved academic resource'}</p><div className="material-card-footer"><span>{m.subject_code||m.subject_name||'AIEMS'}</span><button className="icon-button" title="Download" onClick={()=>downloadMaterial(m)}><Download size={16}/></button></div></article>)}</div>:<EmptyState title="No matching resources" text="Try clearing the search or selecting another category."/>}
  </Dashboard>:<Navigate to="/login" replace/>
}

function Protected({role,children}:{role:Session['user']['role'],children:ReactNode}) {
  const session=getSession()
  return session&&session.user.role===role?children:<Navigate to="/login" replace/>
}

export default function App() {
  return <BrowserRouter><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/login" element={<AuthPage/>}/>
    <Route path="/register" element={<AuthPage register/>}/>
    <Route path="/student" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/teacher" element={<Protected role="TEACHER"><TeacherDashboard/></Protected>}/>
    <Route path="/hod" element={<Protected role="HOD"><HodDashboard/></Protected>}/>
    <Route path="/materials" element={<MaterialsLibrary/>}/>
    <Route path="/student/bookmarks" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/student/profile" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/teacher/upload" element={<Protected role="TEACHER"><TeacherDashboard/></Protected>}/>
    <Route path="/teacher/materials" element={<Protected role="TEACHER"><TeacherDashboard/></Protected>}/>
    <Route path="/teacher/subjects" element={<Protected role="TEACHER"><TeacherDashboard/></Protected>}/>
    <Route path="/hod/teachers" element={<Protected role="HOD"><HodDashboard/></Protected>}/>
    <Route path="/hod/materials" element={<Protected role="HOD"><HodDashboard/></Protected>}/>
    <Route path="/hod/academics" element={<Protected role="HOD"><HodDashboard/></Protected>}/>
    <Route path="/hod/reports" element={<Protected role="HOD"><HodDashboard/></Protected>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></BrowserRouter>
}
