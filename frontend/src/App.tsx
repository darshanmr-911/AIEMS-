import { useEffect, useState } from 'react'
import type { CSSProperties, FormEvent, ReactNode } from 'react'
import { motion } from 'framer-motion'
import { GlassStatCard, pageMotion } from './components/GlassComponents'
import { BrowserRouter, Navigate, Route, Routes, useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import aiemsCampus from './assets/aiems-campus.png'
import {
  ArrowRight, Bell, Bookmark, BookOpen, Building2, ChevronLeft,
  ChevronRight, CircleUserRound, ClipboardList, Download, FileText, GraduationCap,
  KeyRound, LayoutDashboard, Library, LogOut, Menu, Moon, Search,
  Settings, Sun, Users, X,
} from 'lucide-react'
import { api, clearSession, getSession, saveSession, type AppSession } from './lib/api'
import {
  HodAssignmentsContent,
  HodDashboardContent,
  HodMaterialsContent,
  HodReportsContent,
  HodSettingsContent,
  HodTeachersContent,
  HodSubjectsContent,
} from './components/HodAdminContent'

type Session = AppSession
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
  department_name?: string
  semester_number?: number
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
        <a className="button primary compact" href="/login">Department HOD login</a>
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
              <a className="text-link" href="/login">Department HOD login <ArrowRight size={16}/></a>
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
              <a className="department-card" href={`/materials?department__code=${encodeURIComponent(code)}`} key={code}>
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
      <footer className="public-footer" id="contact"><a href="/"><Logo/></a><p>AIEMS College · Your College. Your Learning. Your Future.</p><div><a href="/login">Department HOD login</a><a href="/student/login">Student sign in</a></div></footer>
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

function apiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data
    if (typeof data === 'string') return data
    if (data && typeof data === 'object') {
      const detail = Reflect.get(data, 'detail')
      if (typeof detail === 'string') return detail
      const firstValue = Object.values(data)[0]
      if (typeof firstValue === 'string') return firstValue
      if (Array.isArray(firstValue) && typeof firstValue[0] === 'string') return firstValue[0]
    }
  }
  return error instanceof Error ? error.message : 'Unable to continue. Please try again.'
}

function HodLoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.post<AppSession>('/auth/login/', { email, password })
      saveSession(response.data)
      navigate(response.data.must_change_password ? '/change-password' : '/hod')
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="auth-layout">
      <div className="auth-aside">
        <a href="/"><Logo/></a>
        <div><span className="overline">AIEMS Learning Hub</span><h1>Your department, securely managed.</h1><p>Sign in with your official department HOD email to manage your academic workspace.</p></div>
        <div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div>
      </div>
      <div className="auth-panel">
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-heading"><span>Department HOD access</span><h2>Sign in to AIEMS Hub</h2></div>
          <Field label="Official department email"><input type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="hodcse@aiems.edu.in"/></Field>
          <Field label="Password"><input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)}/></Field>
          {error && <div className="error-message">{error}</div>}
          <button className="button primary full" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'} {!loading && <ArrowRight size={17}/>}</button>
          <a className="auth-switch" href="/password-reset">Forgot password?</a>
          <p className="auth-switch">Looking for study materials? <a href="/materials">Browse the public library</a></p>
        </form>
      </div>
    </div>
  )
}

function StudentLoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.post<AppSession>('/auth/student/login/', { username, password })
      saveSession(response.data)
      navigate(response.data.must_change_password ? '/change-password' : '/student')
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  return <div className="auth-layout">
    <div className="auth-aside"><a href="/"><Logo/></a><div><span className="overline">AIEMS Learning Hub</span><h1>Keep learning with your campus.</h1><p>Student sign-in for existing academic accounts.</p></div><div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div className="auth-heading"><span>Student access</span><h2>Sign in</h2></div>
      <Field label="Username"><input required autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)}/></Field>
      <Field label="Password"><input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)}/></Field>
      {error && <div className="error-message">{error}</div>}
      <button className="button primary full" disabled={loading}>{loading ? 'Please wait…' : 'Sign in'} {!loading && <ArrowRight size={17}/>}</button>
      <p className="auth-switch">Need an account? <a href="/register">Register as a student</a></p>
    </form></div>
  </div>
}

function StudentRegistrationPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '', password: '', password_confirm: '', first_name: '', last_name: '',
    email: '', usn: '', department: '', semester: '', academic_year: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.post('/auth/register/student/', {
        ...form,
        department: Number(form.department),
        semester: Number(form.semester),
      })
      navigate('/student/login')
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }
  return <div className="auth-layout">
    <div className="auth-aside"><a href="/"><Logo/></a><div><span className="overline">AIEMS Learning Hub</span><h1>Start your academic journey.</h1><p>Create a student workspace to keep track of your department resources.</p></div><div className="auth-aside-footer"><span>Student account</span><span>AIEMS · 2026</span></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div className="auth-heading"><span>Student registration</span><h2>Create account</h2></div>
      <div className="form-grid">
        <Field label="First name"><input required value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })}/></Field>
        <Field label="Last name"><input required value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })}/></Field>
        <Field label="Email"><input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}/></Field>
        <Field label="USN"><input required value={form.usn} onChange={(event) => setForm({ ...form, usn: event.target.value })}/></Field>
        <Field label="Department ID"><input type="number" min={1} required value={form.department} onChange={(event) => setForm({ ...form, department: event.target.value })}/></Field>
        <Field label="Semester ID"><input type="number" min={1} required value={form.semester} onChange={(event) => setForm({ ...form, semester: event.target.value })}/></Field>
        <Field label="Academic year"><input required placeholder="2025-2026" value={form.academic_year} onChange={(event) => setForm({ ...form, academic_year: event.target.value })}/></Field>
        <Field label="Username"><input required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })}/></Field>
        <Field label="Password"><input type="password" required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })}/></Field>
        <Field label="Confirm password"><input type="password" required value={form.password_confirm} onChange={(event) => setForm({ ...form, password_confirm: event.target.value })}/></Field>
      </div>
      {error && <div className="error-message">{error}</div>}
      <button className="button primary full" disabled={loading}>{loading ? 'Creating account…' : 'Create student account'} {!loading && <ArrowRight size={17}/>}</button>
      <p className="auth-switch">Already registered? <a href="/student/login">Sign in</a></p>
    </form></div>
  </div>
}

function ChangePasswordPage() {
  const navigate = useNavigate()
  const session = getSession()
  const [form, setForm] = useState({ current_password: '', new_password: '', password_confirm: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  if (!session) return <Navigate to="/login" replace/>
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.post<{ access: string; refresh: string; must_change_password: boolean }>('/auth/password/change/', form)
      saveSession({ ...session, ...response.data })
      navigate(session.user.role === 'HOD' ? '/hod' : '/student')
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }
  return <div className="auth-layout">
    <div className="auth-aside"><a href="/"><Logo/></a><div><span className="overline">Account security</span><h1>One quick security step.</h1><p>Choose a new password before entering your department workspace.</p></div><div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div className="auth-heading"><span>Required password update</span><h2>Change your password</h2></div>
      <Field label="Current password"><input type="password" autoComplete="current-password" required value={form.current_password} onChange={(event) => setForm({ ...form, current_password: event.target.value })}/></Field>
      <Field label="New password"><input type="password" autoComplete="new-password" minLength={8} required value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })}/></Field>
      <Field label="Confirm new password"><input type="password" autoComplete="new-password" minLength={8} required value={form.password_confirm} onChange={(event) => setForm({ ...form, password_confirm: event.target.value })}/></Field>
      {error && <div className="error-message">{error}</div>}
      <button className="button primary full" disabled={loading}>{loading ? 'Updating…' : 'Update password'} {!loading && <KeyRound size={16}/>}</button>
    </form></div>
  </div>
}

function PasswordResetRequestPage() {
  const [email, setEmail] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setNotice('')
    try {
      const response = await api.post<{ detail: string }>('/auth/password/reset/', { email })
      setNotice(response.data.detail)
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }
  return <div className="auth-layout"><div className="auth-aside"><a href="/"><Logo/></a><div><span className="overline">Account recovery</span><h1>We’ll help you get back in.</h1><p>Reset links are sent only to the email address registered to the account.</p></div><div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div className="auth-heading"><span>Password reset</span><h2>Forgot your password?</h2></div>
      <Field label="Account email"><input type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)}/></Field>
      {notice && <div className="success-message" role="status">{notice}</div>}{error && <div className="error-message">{error}</div>}
      <button className="button primary full" disabled={loading}>{loading ? 'Sending…' : 'Send reset link'} {!loading && <ArrowRight size={17}/>}</button>
      <p className="auth-switch"><a href="/login">Return to HOD sign in</a></p>
    </form></div>
  </div>
}

function PasswordResetConfirmPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [form, setForm] = useState({ new_password: '', password_confirm: '' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.post<{ detail: string }>('/auth/password/reset/confirm/', {
        uid: searchParams.get('uid') || '',
        token: searchParams.get('token') || '',
        ...form,
      })
      setNotice(response.data.detail)
    } catch (reason) {
      setError(apiErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }
  return <div className="auth-layout"><div className="auth-aside"><a href="/"><Logo/></a><div><span className="overline">Account recovery</span><h1>Choose a new password.</h1><p>This one-time reset link expires automatically after use.</p></div><div className="auth-aside-footer"><span>Secure campus access</span><span>AIEMS · 2026</span></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div className="auth-heading"><span>Password reset</span><h2>Set a new password</h2></div>
      <Field label="New password"><input type="password" autoComplete="new-password" minLength={8} required value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })}/></Field>
      <Field label="Confirm new password"><input type="password" autoComplete="new-password" minLength={8} required value={form.password_confirm} onChange={(event) => setForm({ ...form, password_confirm: event.target.value })}/></Field>
      {notice && <div className="success-message" role="status">{notice} <button type="button" className="text-button" onClick={() => navigate('/login')}>Sign in</button></div>}
      {error && <div className="error-message">{error}</div>}
      {!notice && <button className="button primary full" disabled={loading}>{loading ? 'Updating…' : 'Reset password'} {!loading && <KeyRound size={16}/>}</button>}
    </form></div>
  </div>
}
function Field({label,children,span=false}:{label:string,children:ReactNode,span?:boolean}) {
  return <label className={span ? 'field span' : 'field'}><span>{label}</span>{children}</label>
}

function Sidebar({role,collapsed,onCollapse}:{role:Session['user']['role'],collapsed:boolean,onCollapse:()=>void}) {
  const navigate=useNavigate()
  const session=getSession()
  const items = role==='HOD'
    ? [['/hod','Overview',LayoutDashboard],['/hod/teachers','Teachers',Users],['/hod/subjects','Subjects',BookOpen],['/hod/assignments','Assignments',ClipboardList],['/hod/materials','Study materials',Library],['/hod/approvals','Approvals',ClipboardList],['/hod/reports','Reports',FileText],['/hod/settings','Settings',Settings]]
    : [['/student','Overview',LayoutDashboard],['/materials','Library',Library],['/student/bookmarks','Bookmarks',Bookmark],['/student/profile','Profile',CircleUserRound]]
  const logout=async()=>{
    try {
      if (session?.refresh) await api.post('/auth/logout/', { refresh: session.refresh })
    } catch (reason) {
      window.alert(`Signed out locally, but the server could not revoke the session: ${apiErrorMessage(reason)}`)
    } finally {
      clearSession()
      navigate('/')
    }
  }
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
  const response = await api.get(`/public/materials/${material.id}/download/`, {
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

function MaterialsLibrary() {
  const [searchParams]=useSearchParams()
  const [materials,setMaterials]=useState<Material[]>([])
  const [query,setQuery]=useState(searchParams.get('q') || '')
  const [category,setCategory]=useState('')
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const departmentCode=searchParams.get('department__code') || ''
  useEffect(()=>{
    api.get('/public/materials/',{params:{search:query||undefined,category:category||undefined,'department__code':departmentCode||undefined}})
      .then(response=>setMaterials(Array.isArray(response.data)?response.data:response.data.results||[]))
      .catch(reason=>setError(apiErrorMessage(reason)))
      .finally(()=>setLoading(false))
  },[query,category,departmentCode])
  const search=(value:string)=>{setLoading(true);setError('');setQuery(value)}
  const selectCategory=(value:string)=>{setLoading(true);setError('');setCategory(value)}
  const download=async(material:Material)=>{
    try { await downloadMaterial(material) } catch(reason) { setError(apiErrorMessage(reason)) }
  }
  return <div className="public-site">
    <PublicHeader/>
    <main className="public-section public-library">
      <div className="section-heading"><div><span>AIEMS Academic Hub</span><h1>{departmentCode ? `${departmentCode} resources` : 'Study material library'}</h1><p>Browse and download approved learning resources from across AIEMS.</p></div></div>
      <section className="library-toolbar" aria-label="Filter study materials">
        <div className="library-search"><Search size={18}/><input aria-label="Search materials" value={query} onChange={event=>search(event.target.value)} placeholder="Search title, subject or subject code"/></div>
        <select aria-label="Filter by category" value={category} onChange={event=>selectCategory(event.target.value)}><option value="">All categories</option><option value="NOTES">Notes</option><option value="PREVIOUS_PAPER">Previous papers</option><option value="MODEL_PAPER">Model papers</option><option value="ASSIGNMENT">Assignments</option><option value="LAB_MANUAL">Lab manuals</option><option value="SYLLABUS">Syllabus</option></select>
      </section>
      {error&&<div className="error-message" role="alert">{error}</div>}
      {loading?<div className="material-card-grid">{[1,2,3,4].map(n=><div className="material-card skeleton" key={n}></div>)}</div>:materials.length?<div className="material-card-grid">{materials.map(m=><article className="material-card" key={m.id}>
        <div className="material-card-top"><div className="file-icon blue"><FileText/></div><span className="category-label">{m.category.replaceAll('_',' ').toLowerCase()}</span></div>
        <h3>{m.title}</h3><p>{m.description||'Approved academic resource'}</p>
        <div className="public-material-meta"><span>{m.subject_code||m.subject_name||'AIEMS'}</span><span>{m.department_name||departmentCode}{m.semester_number?` · Semester ${m.semester_number}`:''}</span></div>
        <div className="material-card-footer"><span>{m.download_count||0} downloads</span><button className="button secondary compact" onClick={()=>void download(m)}><Download size={15}/> Download</button></div>
      </article>)}</div>:<EmptyState title="No matching resources" text="Try clearing the search or selecting another category."/>}
    </main>
    <footer className="public-footer" id="contact"><a href="/"><Logo/></a><p>AIEMS College · Your College. Your Learning. Your Future.</p><div><a href="/login">Department HOD login</a><a href="/student/login">Student sign in</a></div></footer>
  </div>
}

function Protected({role,children}:{role:Session['user']['role'],children:ReactNode}) {
  const session=getSession()
  if (!session) return <Navigate to={role === 'STUDENT' ? '/student/login' : '/login'} replace/>
  if (session.must_change_password) return <Navigate to="/change-password" replace/>
  if (session.user.role !== role) {
    return <Navigate to={session.user.role === 'HOD' ? '/hod' : session.user.role === 'STUDENT' ? '/student' : '/login'} replace/>
  }
  return children
}

export default function App() {
  return <BrowserRouter><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/login" element={<HodLoginPage/>}/>
    <Route path="/student/login" element={<StudentLoginPage/>}/>
    <Route path="/register" element={<StudentRegistrationPage/>}/>
    <Route path="/change-password" element={<ChangePasswordPage/>}/>
    <Route path="/password-reset" element={<PasswordResetRequestPage/>}/>
    <Route path="/password-reset/confirm" element={<PasswordResetConfirmPage/>}/>
    <Route path="/student" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/hod" element={<Protected role="HOD"><Dashboard role="HOD" title="Department overview" subtitle="Your department at a glance"><HodDashboardContent/></Dashboard></Protected>}/>
    <Route path="/materials" element={<MaterialsLibrary/>}/>
    <Route path="/student/bookmarks" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/student/profile" element={<Protected role="STUDENT"><StudentDashboard/></Protected>}/>
    <Route path="/hod/teachers" element={<Protected role="HOD"><Dashboard role="HOD" title="Teacher management" subtitle="Manage accounts and assignments in your department"><HodTeachersContent/></Dashboard></Protected>}/>
    <Route path="/hod/subjects" element={<Protected role="HOD"><Dashboard role="HOD" title="Subject management" subtitle="Organize department semesters and subjects"><HodSubjectsContent/></Dashboard></Protected>}/>
    <Route path="/hod/assignments" element={<Protected role="HOD"><Dashboard role="HOD" title="Teacher assignments" subtitle="Assign department subjects to teachers"><HodAssignmentsContent/></Dashboard></Protected>}/>
    <Route path="/hod/materials" element={<Protected role="HOD"><Dashboard role="HOD" title="Study materials" subtitle="Upload resources and review teacher submissions"><HodMaterialsContent/></Dashboard></Protected>}/>
    <Route path="/hod/approvals" element={<Protected role="HOD"><Dashboard role="HOD" title="Material approvals" subtitle="Review submissions from your department"><HodMaterialsContent initialStatus="PENDING"/></Dashboard></Protected>}/>
    <Route path="/hod/reports" element={<Protected role="HOD"><Dashboard role="HOD" title="Department reports" subtitle="Review department-specific activity and totals"><HodReportsContent/></Dashboard></Protected>}/>
    <Route path="/hod/settings" element={<Protected role="HOD"><Dashboard role="HOD" title="Account settings" subtitle="Manage your department HOD account"><HodSettingsContent/></Dashboard></Protected>}/>
    <Route path="/hod/academics" element={<Protected role="HOD"><Navigate to="/hod/subjects" replace/></Protected>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></BrowserRouter>
}
