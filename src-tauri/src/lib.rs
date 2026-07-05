use std::process::{Child, Command};
use std::sync::Mutex;
use std::net::TcpListener;
use tauri::{Manager, State, RunEvent};

struct ServerState {
    child: Mutex<Option<Child>>,
    port: u16,
}

fn get_free_port() -> Option<u16> {
    TcpListener::bind("127.0.0.1:0")
        .and_then(|listener| listener.local_addr())
        .map(|addr| addr.port())
        .ok()
}

#[tauri::command]
fn get_server_port(state: State<'_, ServerState>) -> u16 {
    state.port
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = get_free_port().unwrap_or(5678);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(ServerState {
            child: Mutex::new(None),
            port,
        })
        .invoke_handler(tauri::generate_handler![get_server_port])
        .setup(move |app| {
            let python_path = "agent/.venv/bin/python3";
            let script_path = "agent/server.py";

            // Spawn the python REST server as a background sidecar
            let child = Command::new(python_path)
                .arg(script_path)
                .arg("--port")
                .arg(port.to_string())
                .spawn();

            match child {
                Ok(c) => {
                    println!("Python server spawned successfully on port {}", port);
                    let state = app.state::<ServerState>();
                    *state.child.lock().unwrap() = Some(c);
                }
                Err(e) => {
                    eprintln!("Failed to spawn Python server process: {:?}", e);
                }
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |app_handle, event| {
            if let RunEvent::Exit = event {
                let state = app_handle.state::<ServerState>();
                let mut lock = state.child.lock().unwrap();
                if let Some(mut child) = lock.take() {
                    println!("Tauri exiting. Cleaning up Python subprocess...");
                    let _ = child.kill();
                }
            }
        });
}
