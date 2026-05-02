use std::process::{Command, Stdio};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(

        let python_cmd = if which::which("python3").is_ok() {
        let mut cmd = Command::new(python_cmd);
  tauri::Builder::default()
    .plugin(
      tauri_plugin_log::Builder::default()
        .level(log::LevelFilter::Info)
        .build(),
    )
    .plugin(tauri_plugin_shell::init())
    .setup(|app| {
      let app_handle = app.handle().clone();

      tauri::async_runtime::spawn(async move {
        if let Err(error) = spawn_backend(app_handle).await {
          log::error!("{}", error);
        }
      });

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
          #[cfg_attr(mobile, tauri::mobile_entry_point)]
          pub fn run() {
            tauri::Builder::default()
              .plugin(
                tauri_plugin_log::Builder::default()
                  .level(log::LevelFilter::Info)
                  .build(),
              )
              .plugin(tauri_plugin_shell::init())
              .setup(|app| {
                let app_handle = app.handle().clone();

                tauri::async_runtime::spawn(async move {
                  if let Err(error) = spawn_backend(app_handle).await {
                    log::error!("{}", error);
                  }
                });

                Ok(())
              })
              .run(tauri::generate_context!())
              .expect("error while running tauri application");
          }

          async fn spawn_backend(app_handle: tauri::AppHandle) -> Result<(), String> {
            match spawn_backend_sidecar(&app_handle).await {
              Ok(()) => Ok(()),
              Err(error) => {
                log::warn!(
                  "[Backend] Sidecar unavailable, falling back to bundled resources: {}",
                  error
                );
                spawn_backend_from_resources(&app_handle).await
              }
            }
          }

          async fn spawn_backend_sidecar(app_handle: &tauri::AppHandle) -> Result<(), String> {
            let command = app_handle
              .shell()
              .sidecar("backend")
              .map_err(|error| format!("[Backend] Sidecar unavailable: {error}"))?;

            let (mut rx, child) = command
              .spawn()
              .map_err(|error| format!("[Backend] Failed to spawn sidecar: {error}"))?;

            log::info!("[Backend] Started sidecar backend process (PID: {})", child.pid());

            tauri::async_runtime::spawn(async move {
              while let Some(event) = rx.recv().await {
                match event {
                  CommandEvent::Stdout(line) => {
                    log::info!("[Backend] {}", String::from_utf8_lossy(&line).trim_end());
                  }
                  CommandEvent::Stderr(line) => {
                    log::warn!("[Backend] {}", String::from_utf8_lossy(&line).trim_end());
                  }
                  CommandEvent::Error(error) => {
                    log::error!("[Backend] Sidecar error: {}", error);
                  }
                  CommandEvent::Terminated(payload) => {
                    if payload.code == Some(0) {
                      log::info!("[Backend] Sidecar exited successfully");
                    } else {
                      log::warn!("[Backend] Sidecar exited with code: {:?}", payload.code);
                    }
                  }
                }
              }
            });

            Ok(())
          }

          async fn spawn_backend_from_resources(app_handle: &tauri::AppHandle) -> Result<(), String> {
            let backend_dir = app_handle
              .path()
              .resolve("backend", BaseDirectory::Resource)
              .map_err(|error| format!("[Backend] Failed to resolve bundled backend: {error}"))?;

            log::info!("[Backend] Starting from bundled resources: {}", backend_dir.display());

            let python_cmd = if which::which("python3").is_ok() {
              "python3"
            } else if which::which("python").is_ok() {
              "python"
            } else {
              return Err("[Backend] Python not found in PATH".to_string());
            };

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
                log::info!("[Backend] Started bundled backend process (PID: {})", child.id());

                match child.wait() {
                  Ok(status) if status.success() => {
                    log::info!("[Backend] Backend exited successfully");
                    Ok(())
                  }
                  Ok(status) => {
                    log::warn!("[Backend] Backend exited with code: {}", status);
                    Ok(())
                  }
                  Err(error) => Err(format!("[Backend] Failed to wait for backend: {error}")),
                }
              }
              Err(error) => Err(format!("[Backend] Failed to spawn backend: {error}")),
            }
          }
