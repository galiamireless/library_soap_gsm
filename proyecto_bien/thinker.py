from __future__ import annotations

import json
import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from werkzeug.serving import make_server

from apps.services.authors.app import app as authors_app
from apps.services.login.app import app as login_app
from apps.services.orders.app import app as orders_app
from apps.services.payments.app import app as payments_app
from apps.services.soap.app import app as soap_app
from apps.services.users.app import app as users_app


SERVICE_APPS = (
    ("Login", login_app, int(login_app.config.get("PORT", 5000)), "/health", True),
    ("SOAP / Books", soap_app, int(soap_app.config.get("PORT", 5001)), "/health?format=json", True),
    ("Users", users_app, 5005, "/health", True),
    ("Authors", authors_app, 5006, "/health", True),
    ("Orders", orders_app, 5007, "/health", True),
    ("Payments", payments_app, 5008, "/health", True),
)

RESOURCES = (
    {
        "name": "Books · SOAP",
        "base": "http://127.0.0.1:5001",
        "collection": "/books?format=json",
        "result_key": "books",
        "key": "isbn",
        "fields": [
            ("isbn", "ISBN", "text"), ("title", "Título", "text"),
            ("author", "Autor", "text"), ("publisher", "Editorial", "text"),
            ("publicationYear", "Año", "int"), ("price", "Precio", "float"),
            ("stock", "Existencias", "int"), ("description", "Descripción", "text"),
            ("format", "Formato", "text"),
        ],
    },
    {
        "name": "Login · Cuentas",
        "base": "http://127.0.0.1:5000",
        "collection": "/admin/users?format=json",
        "result_key": "items",
        "key": "user_id",
        "fields": [
            ("first_name", "Nombre", "text"), ("last_name", "Apellido paterno", "text"),
            ("maternal_last_name", "Apellido materno", "text"), ("email", "Correo", "text"),
            ("password", "Contraseña nueva", "password"), ("role_id", "Rol (1/2/3)", "int"),
        ],
    },
    {
        "name": "Users · Perfiles",
        "base": "http://127.0.0.1:5005",
        "collection": "/users",
        "result_key": "items",
        "key": "id",
        "fields": [("name", "Nombre", "text"), ("email", "Correo", "text"), ("password", "Contraseña", "password"), ("role_id", "Rol (1/2/3)", "int")],
    },
    {
        "name": "Authors",
        "base": "http://127.0.0.1:5006",
        "collection": "/authors",
        "result_key": "items",
        "key": "id",
        "fields": [("name", "Nombre", "text"), ("country", "País", "text")],
    },
    {
        "name": "Orders",
        "base": "http://127.0.0.1:5007",
        "collection": "/orders",
        "result_key": "items",
        "key": "id",
        "fields": [("customer_name", "Cliente", "text"), ("items", "Artículos JSON", "json"), ("status", "Estado", "text")],
    },
    {
        "name": "Payments",
        "base": "http://127.0.0.1:5008",
        "collection": "/payments",
        "result_key": "items",
        "key": "id",
        "fields": [("order_id", "ID pedido", "int"), ("amount", "Importe", "float"), ("method", "Método", "text")],
    },
)


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def api_request(method: str, url: str, token: str = "", payload=None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, method=method)
    request.add_header("Accept", "application/json")
    if body is not None:
        request.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=4) as response:
            raw = response.read()
            if not raw:
                return {}
            decoded = raw.decode("utf-8", errors="replace")
            try:
                return json.loads(decoded)
            except json.JSONDecodeError:
                return {"raw": decoded}
    except HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("error", raw)
        except ValueError:
            detail = raw
        raise ApiError(error.code, str(detail or error.reason)) from error
    except (URLError, TimeoutError, OSError) as error:
        raise ApiError(0, f"No se pudo contactar {url}: {error}") from error


class ManagedServices:
    def __init__(self, log):
        self.log = log
        self.servers = []
        self.states = {name: "starting" for name, *_ in SERVICE_APPS}
        self.stop_event = threading.Event()

    @staticmethod
    def port_is_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return True
        except OSError:
            return False

    def start(self):
        for name, flask_app, port, _, _ in SERVICE_APPS:
            if self.port_is_open(port):
                self.states[name] = "external"
                self.log(f"{name}: puerto {port} ya estaba ocupado; se usará el servicio existente.")
                continue
            try:
                server = make_server("127.0.0.1", port, flask_app, threaded=True)
                thread = threading.Thread(target=server.serve_forever, name=f"thinker-{name}", daemon=True)
                thread.start()
                self.servers.append(server)
                self.states[name] = "managed"
                self.log(f"{name}: iniciado en http://127.0.0.1:{port}")
            except OSError as error:
                self.states[name] = "down"
                self.log(f"{name}: no se pudo iniciar en :{port} ({error}).")

    def probe_all(self):
        results = {}
        for name, _, port, health_path, _ in SERVICE_APPS:
            try:
                api_request("GET", f"http://127.0.0.1:{port}{health_path}")
                results[name] = "up"
            except ApiError:
                results[name] = "down"
        try:
            with socket.create_connection(("127.0.0.1", 6379), timeout=0.4) as redis_socket:
                redis_socket.sendall(b"*1\r\n$4\r\nPING\r\n")
                results["Redis"] = "up" if redis_socket.recv(16).startswith(b"+PONG") else "optional"
        except OSError:
            results["Redis"] = "optional"
        return results

    def stop(self):
        self.stop_event.set()
        for server in reversed(self.servers):
            try:
                server.shutdown()
                server.server_close()
            except OSError:
                pass
        self.servers.clear()
        try:
            soap_app.extensions["repository"].close()
        except Exception:
            pass


class ResourceTab(ttk.Frame):
    def __init__(self, parent, app: "ThinkerApp", config: dict):
        super().__init__(parent, padding=10)
        self.owner = app
        self.config_data = config
        self.fields = {field[0]: field for field in config["fields"]}
        self.variables = {}
        self.build_form()
        self.build_table()

    def build_form(self):
        form = ttk.LabelFrame(self, text="Formulario", padding=10)
        form.pack(fill="x", pady=(0, 9))
        columns = 3
        for index, (key, label, kind) in enumerate(self.config_data["fields"]):
            row, column = divmod(index, columns)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=column, sticky="ew", padx=6, pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            variable = tk.StringVar()
            self.variables[key] = variable
            if key == "items":
                variable.set('[{"book_isbn":"9781234567890","quantity":1,"price":150}]')
            elif key == "order_id":
                variable.set("1")
            elif key == "amount":
                variable.set("150")
            elif key == "method":
                variable.set("card")
            elif key == "status":
                variable.set("pending")
            elif key == "role_id":
                variable.set("3")
            entry = ttk.Entry(cell, textvariable=variable, show="*" if kind == "password" else "")
            entry.pack(fill="x")
        for column in range(columns):
            form.columnconfigure(column, weight=1)
        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(0, 9))
        actions = (
            ("Actualizar lista", self.refresh),
            ("Crear", self.create),
            ("Guardar cambios", self.update),
            ("Eliminar", self.delete),
            ("Limpiar", self.clear),
        )
        for label, command in actions:
            ttk.Button(button_row, text=label, command=command).pack(side="left", padx=(0, 6))
        self.message = ttk.Label(button_row, text="", anchor="e")
        self.message.pack(side="right", fill="x", expand=True)

    def build_table(self):
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        self.columns = [self.config_data["key"], *[field[0] for field in self.config_data["fields"] if field[0] != self.config_data["key"] and field[2] != "password"]]
        self.table = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        for key in self.columns:
            label = self.fields[key][1] if key in self.fields else "ID"
            self.table.heading(key, text=label)
            self.table.column(key, width=140, minwidth=80, stretch=True)
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.table.bind("<<TreeviewSelect>>", self.select_row)

    def endpoint(self, identifier=None):
        base = self.config_data["base"] + self.config_data["collection"].split("?")[0]
        if identifier is not None:
            base += "/" + quote(str(identifier), safe="")
        if "?" in self.config_data["collection"]:
            base += "?" + self.config_data["collection"].split("?", 1)[1]
        return base

    def payload(self):
        result = {}
        for key, (_field_label, kind) in self.fields.items():
            value = self.variables[key].get().strip()
            if kind == "password" and not value:
                continue
            if kind == "int" and value:
                result[key] = int(value)
            elif kind == "float" and value:
                result[key] = float(value)
            elif kind == "json" and value:
                result[key] = json.loads(value)
            elif value:
                result[key] = value
        return result

    def run_api(self, method, url, payload=None, success=None):
        self.message.configure(text="Procesando…")
        token = self.owner.token.get()
        self.owner.run_async(
            lambda: api_request(method, url, token, payload),
            on_success=success or (lambda _: self.refresh()),
            on_error=self.show_error,
        )

    def show_error(self, error):
        self.message.configure(text=f"Error: {error}")
        self.owner.log(f"{self.config_data['name']}: {error}")

    def refresh(self):
        def loaded(data):
            items = data.get(self.config_data["result_key"], [])
            self.table.delete(*self.table.get_children())
            for item in items:
                values = []
                for key in self.columns:
                    value = item.get(key, "")
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    values.append(value)
                self.table.insert("", "end", values=values)
            self.message.configure(text=f"{len(items)} registros")
        self.run_api("GET", self.endpoint(), success=loaded)

    def create(self):
        try:
            data = self.payload()
        except (ValueError, json.JSONDecodeError) as error:
            self.show_error(f"Revisa los datos del formulario: {error}")
            return
        self.run_api("POST", self.endpoint(), data)

    def selected_id(self):
        selected = self.table.selection()
        return self.table.item(selected[0], "values")[0] if selected else None

    def update(self):
        identifier = self.selected_id()
        if identifier is None:
            self.show_error("Selecciona un registro de la tabla.")
            return
        try:
            data = self.payload()
        except (ValueError, json.JSONDecodeError) as error:
            self.show_error(f"Revisa los datos del formulario: {error}")
            return
        self.run_api("PUT", self.endpoint(identifier), data)

    def delete(self):
        identifier = self.selected_id()
        if identifier is None:
            self.show_error("Selecciona un registro de la tabla.")
            return
        if not messagebox.askyesno("Confirmar eliminación", f"¿Eliminar el registro {identifier}?"):
            return
        self.run_api("DELETE", self.endpoint(identifier))

    def select_row(self, event=None):
        table = event.widget if event is not None else self.table
        selected = table.selection()
        if not selected:
            return
        values = table.item(selected[0], "values")
        current = dict(zip(self.columns, values))
        for key, variable in self.variables.items():
            if key == "password":
                variable.set("")
            elif key in current:
                variable.set(current[key])
            elif key == "items":
                variable.set("[]")

    def clear(self):
        for variable in self.variables.values():
            variable.set("[]" if self.fields[variable_key(self.variables, variable)][2] == "json" else "")
        self.table.selection_remove(self.table.selection())
        self.message.configure(text="")


def variable_key(variables, selected):
    return next(key for key, variable in variables.items() if variable is selected)


class ThinkerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Thinker | Consola de microservicios")
        self.root.geometry("1380x850")
        self.root.minsize(1080, 700)
        self.events = queue.Queue()
        self.token = tk.StringVar(value="")
        self.service_indicators = {}
        self.log_text = None
        self.services = ManagedServices(self.log)
        self.configure_style()
        self.build_header()
        self.build_auth_panel()
        self.build_tabs()
        self.build_log()
        self.services.start()
        self.root.after(250, self.drain_events)
        self.root.after(700, self.poll_health)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def configure_style(self):
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#20263a")
        style.configure("SubTitle.TLabel", font=("Segoe UI", 9), foreground="#606b7c")
        style.configure("Semaphore.TLabel", font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def build_header(self):
        header = ttk.Frame(self.root, padding=(14, 10))
        header.pack(fill="x")
        title_area = ttk.Frame(header)
        title_area.pack(side="left", fill="x", expand=True)
        ttk.Label(title_area, text="Thinker", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_area, text="Microservicios · CRUD · JWT · Redis", style="SubTitle.TLabel").pack(anchor="w")
        status_area = ttk.Frame(header)
        status_area.pack(side="right")
        for name, _, _, _, _ in SERVICE_APPS:
            self.add_indicator(status_area, name)
        self.add_indicator(status_area, "Redis", optional=True)

    def add_indicator(self, parent, name, optional=False):
        item = ttk.Frame(parent, padding=(5, 2))
        item.pack(side="left")
        dot = ttk.Label(item, text="●", foreground="#a0a7b3", style="Semaphore.TLabel")
        dot.pack(side="left", padx=(0, 4))
        text = ttk.Label(item, text=name, style="Semaphore.TLabel")
        text.pack(side="left")
        self.service_indicators[name] = (dot, text, optional)

    def build_auth_panel(self):
        panel = ttk.LabelFrame(self.root, text="Sesión de administración", padding=8)
        panel.pack(fill="x", padx=14, pady=(0, 8))
        self.admin_name = tk.StringVar()
        self.admin_email = tk.StringVar()
        self.admin_password = tk.StringVar()
        for index, (label, variable, show) in enumerate((
            ("Nombre para primer inicio", self.admin_name, ""),
            ("Correo", self.admin_email, ""),
            ("Contraseña", self.admin_password, "*"),
        )):
            cell = ttk.Frame(panel)
            cell.grid(row=0, column=index, sticky="ew", padx=5)
            ttk.Entry(cell, textvariable=variable, show=show).pack(fill="x")
        ttk.Button(panel, text="Crear primer administrador", command=self.bootstrap).grid(row=0, column=3, padx=5, pady=(14, 0))
        ttk.Button(panel, text="Iniciar sesión", command=self.login).grid(row=0, column=4, padx=5, pady=(14, 0))
        self.session_label = ttk.Label(panel, text="Sin sesión", style="SubTitle.TLabel")
        self.session_label.grid(row=0, column=6, padx=10, pady=(14, 0), sticky="e")
        panel.columnconfigure(6, weight=1)

    def build_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=5)
        self.resource_tabs = {}
        for config in RESOURCES:
            tab = ResourceTab(self.tabs, self, config)
            self.tabs.add(tab, text=config["name"])
            self.resource_tabs[config["name"]] = tab
        login_tools = ttk.Frame(self.tabs, padding=10)
        ttk.Label(login_tools, text="Verificación de correo de una cuenta Login", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(login_tools)
        row.pack(fill="x")
        self.verification_token = tk.StringVar()
        ttk.Entry(row, textvariable=self.verification_token).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Verificar correo", command=self.verify_email).pack(side="left")
        ttk.Label(login_tools, text="En modo console, copia el token impreso en la terminal del servicio Login.", style="SubTitle.TLabel").pack(anchor="w", pady=8)
        self.tabs.insert(1, login_tools, text="Login · Verificación")

    def build_log(self):
        frame = ttk.LabelFrame(self.root, text="Actividad", padding=5)
        frame.pack(fill="x", padx=14, pady=(4, 10))
        self.log_text = tk.Text(frame, height=5, wrap="word", state="disabled", font=("Consolas", 9), background="#f4f6fa")
        self.log_text.pack(fill="x")

    def log(self, message):
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def run_async(self, work, on_success=None, on_error=None):
        def worker():
            try:
                value = work()
                self.events.put((on_success, on_error, value, None))
            except Exception as error:
                self.events.put((on_success, on_error, None, error))
        threading.Thread(target=worker, daemon=True).start()

    def drain_events(self):
        try:
            while True:
                on_success, on_error, value, error = self.events.get_nowait()
                if error is not None:
                    if on_error:
                        on_error(error)
                    self.log(str(error))
                elif on_success:
                    on_success(value)
        except queue.Empty:
            pass
        self.root.after(100, self.drain_events)

    def bootstrap(self):
        name, email, password = self.admin_name.get().strip(), self.admin_email.get().strip(), self.admin_password.get()
        if not name or not email or len(password) < 8:
            messagebox.showerror("Datos incompletos", "Captura nombre, correo y contraseña de al menos 8 caracteres.")
            return
        def success(response):
            self.log(response.get("message", "Administrador inicial creado.") + " Iniciando sesión.")
            self.login()
        self.run_async(lambda: api_request("POST", "http://127.0.0.1:5005/bootstrap", payload={"name": name, "email": email, "password": password}), success, lambda error: messagebox.showerror("No se pudo configurar", str(error)))

    def login(self):
        email, password = self.admin_email.get().strip(), self.admin_password.get()
        if not email or not password:
            messagebox.showerror("Faltan credenciales", "Captura correo y contraseña.")
            return
        def success(response):
            self.token.set(response["token"])
            user = response.get("user", {})
            self.session_label.configure(text=f"{user.get('email', email)} · rol {user.get('role_id', '?')}")
            self.log("Sesión iniciada; el token se mantiene solo en memoria.")
            for tab in self.resource_tabs.values():
                tab.refresh()
        self.run_async(lambda: api_request("POST", "http://127.0.0.1:5005/login", payload={"email": email, "password": password}), success, lambda error: messagebox.showerror("Login rechazado", str(error)))

    def logout(self):
        self.token.set("")
        self.session_label.configure(text="Sin sesión")
        self.log("Sesión local cerrada; el token fue eliminado de la GUI.")

    def verify_email(self):
        token = self.verification_token.get().strip()
        if not token:
            messagebox.showerror("Falta token", "Pega el token de verificación.")
            return
        url = "http://127.0.0.1:5000/verify-email?format=json&token=" + quote(token, safe="")
        self.run_async(lambda: api_request("GET", url), lambda response: self.log(response.get("email", "Cuenta Login verificada.")), lambda error: messagebox.showerror("No se pudo verificar", str(error)))

    def poll_health(self):
        def completed(results):
            colors = {"up": "#168a52", "down": "#c93b43", "optional": "#d28a26"}
            for name, state in results.items():
                indicator = self.service_indicators.get(name)
                if indicator:
                    dot, label, optional = indicator
                    dot.configure(foreground=colors[state])
                    label.configure(foreground=colors[state])
                    label.configure(text="Redis opcional" if optional and state == "optional" else name)
        self.run_async(self.services.probe_all, completed)
        self.root.after(6000, self.poll_health)

    def close(self):
        if messagebox.askokcancel("Cerrar Thinker", "Se detendrán los servicios que inició esta ventana."):
            self.services.stop()
            self.root.destroy()


def main():
    root = tk.Tk()
    ThinkerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
