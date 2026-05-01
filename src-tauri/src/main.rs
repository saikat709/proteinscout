// src-tauri/src/main.rs
// Prevents console window from appearing on Windows
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child};
use std::sync::Mutex;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle();

            // Resolve path to the bundled Python backend
            let resource_path = handle
                .path_resolver()
                .resolve_resource("backend/")
                .expect("Failed to resolve backend resource path");

            // Launch uvicorn (Python FastAPI backend)
            // In production build, Python is bundled as a sidecar binary
            let child = Command::new("python")
                .args([
                    "-m", "uvicorn",
                    "main:app",
                    "--port", "8000",
                    "--host", "127.0.0.1",
                ])
                .current_dir(&resource_path)
                .spawn()
                .expect("Failed to start Python backend");

            *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);

            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::Destroyed = event.event() {
                // Kill backend process when window closes
                if let Some(mut child) = event
                    .window()
                    .app_handle()
                    .state::<BackendProcess>()
                    .0
                    .lock()
                    .unwrap()
                    .take()
                {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
