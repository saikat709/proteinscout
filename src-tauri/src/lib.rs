use std::process::{Command, Stdio};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(
      tauri_plugin_log::Builder::default()
        .level(log::LevelFilter::Info)
        .build(),
    )
    .setup(|_app| {
      // Spawn backend Python process
      tauri::async_runtime::spawn(async {
        // Use /backend folder (same in dev and build)
        let backend_dir = if cfg!(debug_assertions) {
          "../backend".to_string()
        } else {
          // In production, backend is bundled with the app
          // Using relative path from the app binary location
          std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            .map(|p| p.join("backend").to_string_lossy().to_string())
            .unwrap_or_else(|| "./backend".to_string())
        };

        log::info!("[Backend] Starting from: {}", backend_dir);

        // Try python3 first, then python
        let python_cmd = if which::which("python3").is_ok() {
          "python3"
        } else if which::which("python").is_ok() {
          "python"
        } else {
          log::error!("[Backend] Python not found in PATH");
          return;
        };

        // Spawn backend
        let mut cmd = Command::new(python_cmd);
        cmd
          .arg("-m")
          .arg("uvicorn")
          .arg("main:app")
          .arg("--host")
          .arg("127.0.0.1")
          .arg("--port")
          .arg("8000")
          .arg("--log-level")
          .arg("info")
          .current_dir(&backend_dir)
          .stdout(Stdio::piped())
          .stderr(Stdio::piped());

        match cmd.spawn() {
          Ok(mut child) => {
            log::info!("[Backend] Started backend process (PID: {})", child.id());
            
            // Wait for process (will block until backend exits)
            match child.wait() {
              Ok(status) => {
                if status.success() {
                  log::info!("[Backend] Backend exited successfully");
                } else {
                  log::warn!("[Backend] Backend exited with code: {}", status);
                }
              }
              Err(e) => {
                log::error!("[Backend] Failed to wait for backend: {}", e);
              }
            }
          }
          Err(e) => {
            log::error!("[Backend] Failed to spawn backend: {}", e);
            log::error!("[Backend] Make sure Python is installed and /backend folder exists");
          }
        }
      });

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
