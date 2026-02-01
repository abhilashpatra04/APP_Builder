import streamlit as st
import time
from api_client import APIClient

st.set_page_config(page_title="App Builder IDE", layout="wide", initial_sidebar_state="expanded")

# --- CSS for "IDE-like" look ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    div[data-testid="stSidebar"] { min-width: 300px; }
    textarea { font-family: 'Fira Code', 'Courier New', monospace !important; font-size: 14px !important; }
    .stCode { font-family: 'Fira Code', 'Courier New', monospace !important; }
</style>
""", unsafe_allow_html=True)

# --- Session State Init ---
if "api" not in st.session_state:
    st.session_state.api = APIClient()

if "token" not in st.session_state:
    st.session_state.token = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

api = st.session_state.api
if st.session_state.token:
    api.set_token(st.session_state.token)


# --- Auth Pages ---
def login_page():
    st.title("App Builder - Login")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary"):
            data = api.login(email, password)
            if data:
                st.session_state.token = data["access_token"]
                st.session_state.user = api.get_me()
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            if api.register(email, password):
                st.success("Registered! Login to continue.")
            else:
                st.error("Registration failed")

# --- Main IDE Layout ---
def ide_page():
    # --- Sidebar: Project & Files ---
    with st.sidebar:
        st.header("📂 Explorer")
        
        projects = api.get_projects()
        project_options = {f"{p['name']} ({p['id'][:4]})": p['id'] for p in projects}
        
        # Add "New Project" as the first option
        project_keys = ["+ New Project"] + list(project_options.keys())
        
        # Determine default index
        idx = 0
        if "current_project" in st.session_state:
            ids = list(project_options.values())
            if st.session_state.current_project in ids:
                # Find matching name
                name = [k for k, v in project_options.items() if v == st.session_state.current_project][0]
                idx = project_keys.index(name)
                
        selected_p_name = st.selectbox("Project", project_keys, index=idx)
        
        if selected_p_name == "+ New Project":
            st.session_state.current_project = "NEW"
            is_new_project = True
        else:
            selected_p_id = project_options[selected_p_name]
            st.session_state.current_project = selected_p_id
            is_new_project = False
            
            # --- Project Status in Sidebar ---
            pid = selected_p_id
            status = api.get_project_status(pid)
            if not status:
                st.error("Project not found")
                return
                
            st.caption(f"Status: **{status['status']}**")
            
            if st.button("🔄 Refresh"):
                st.rerun()
                
            st.divider()
            
            # --- File Tree in Sidebar ---
            st.subheader("Files")
            if status['completed_files'] > 0 or status['total_files'] > 0:
                files = api.get_files(pid)
                if files:
                    file_paths = [f['path'] for f in files]
                    
                    # Build tree structure
                    tree = {}
                    for path in file_paths:
                        parts = path.split('/')
                        current = tree
                        for part in parts:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                    
                    # Recursive render function
                    def render_tree(node, current_path=""):
                        for name, children in sorted(node.items()):
                            full_path = f"{current_path}/{name}" if current_path else name
                            if children:  # Directory
                                with st.expander(f"� {name}", expanded=False):
                                    render_tree(children, full_path)
                            else:  # File
                                if st.button(f"📄 {name}", key=full_path, use_container_width=True):
                                    st.session_state.selected_file = full_path

                    render_tree(tree)
                else:
                    st.info("No files generated yet")
            else:
                 st.info("No files yet")

        if st.button("🚪 Logout"):
            st.session_state.token = None
            st.rerun()

    # --- Main Area ---
    if is_new_project:
        # Show Create Project Form in Main Area
        st.header("🚀 Start New Project")
        
        with st.form("new_project_form"):
            new_prompt = st.text_area("What do you want to build?", height=150, placeholder="e.g. A responsive portfolio website for a photographer with a gallery and contact form.")
            new_name = st.text_input("Project Name (optional)")
            submitted = st.form_submit_button("Start Building", type="primary")
            
            if submitted:
                if new_prompt:
                    with st.spinner("Initializing project..."):
                        resp = api.create_project_v2(new_prompt, new_name)
                        if resp and "project_id" in resp:
                            st.session_state.current_project = resp['project_id']
                            st.success(f"Project initialized! ID: {resp['project_id']}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to create project. Check server logs.")
                else:
                    st.warning("Please describe what you want to build.")
    
    else:
        # Show IDE Interface (Use stored pid from sidebar selection)
        pid = st.session_state.current_project
        show_ide_interface(pid, status)


def show_ide_interface(pid, status):
    # col_main (Editor/Preview) | col_chat (Chat)
    col_main, col_chat = st.columns([2, 1])
    
    with col_main:
        s_val = status['status']
        
        if s_val == "planning":
            st.info("🧠 AI is planning your application...")
            with st.spinner("Generating plan..."):
                time.sleep(2)
                st.rerun()
                
        elif s_val == "plan_review":
            st.subheader("📋 Plan Review")
            plan = api.get_plan(pid)
            if plan:
                with st.expander("Project Details", expanded=True):
                    st.write(f"**Description:** {plan.get('description')}")
                    st.write(f"**Tech Stack:** {plan.get('required_tech_stacks') or plan.get('tech_stacks')}")
                
                st.write("**Proposed Files:**")
                for f in plan.get('files', []):
                    st.markdown(f"- `{f['path']}`: {f['purpose']}")
                    
                if st.button("✅ Approve Plan", type="primary", use_container_width=True):
                    api.approve_plan(pid)
                    st.success("Plan Approved!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("⚠️ Plan data not found. Please try refreshing.")
                    
        elif s_val == "architecting":
            st.info("🏗️ AI is architecting the solution...")
            with st.spinner("Breaking down tasks..."):
                time.sleep(2)
                st.rerun()

        elif s_val == "task_review":
            st.subheader("✅ Implementation Plan")
            tasks = api.get_tasks(pid)
            if tasks:
                task_list = tasks.get('implementation_steps', [])
                for i, task in enumerate(task_list):
                     st.info(f"**{i+1}. {task['filepath']}**: {task['task_description']}")
                
                if st.button("✅ Start Coding", type="primary", use_container_width=True):
                     api.approve_tasks(pid)
                     st.success("Coding Started!")
                     time.sleep(1)
                     st.rerun()
            else:
                 st.error("⚠️ Task data not found. Please try refreshing.")
                     
        elif s_val in ["coding", "generating"]:
            st.info("🔨 AI is writing code...")
            time.sleep(2)
            st.rerun()
            # progress bar simulation could go here
            if st.session_state.selected_file:
                show_editor(pid)
            else:
                st.write("Select a file from the sidebar to view progress.")
                
        elif s_val in ["completed", "failed"]:
            if st.session_state.selected_file:
                show_editor(pid)
            else:
                st.info("👈 Select a file from the sidebar to view/edit.")
                st.markdown("### Project Completed! 🚀")

    # --- Chat Panel (Right) ---
    with col_chat:
        st.subheader("💬 AI Chat")
        
        # Chat container to keep messages
        chat_container = st.container(height=600)
        
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Chat Input
        if prompt := st.chat_input("Ask about code or req. changes..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        resp = api.chat_edit(pid, prompt)
                        reply = resp.get("response", "Processing...") if resp else "Connection failed"
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        if resp and "diff" in resp:
                             st.code(resp["diff"], language="diff")

def show_editor(pid):
    fpath = st.session_state.selected_file
    st.subheader(f"📝 {fpath}")
    
    content = api.get_file_content(pid, fpath)
    
    ext = fpath.split('.')[-1]
    lang = "python" if ext == "py" else "javascript" if ext in ["js", "jsx"] else "html"
    
    st.code(content, language=lang, line_numbers=True)

# --- Routing ---
if not st.session_state.token:
    login_page()
else:
    ide_page()
