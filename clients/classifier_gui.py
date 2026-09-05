import tkinter as tk
from tkinter import messagebox

from clients.desktop_client import LibrarySoapClient, SoapClientError


def run():
    root = tk.Tk()
    root.title("Clasificador Cloud SOAP")
    fields = {}
    for row, label in enumerate(("Nombre", "Apellidos", "Correo", "ISBN", "ID concepto")):
        tk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=5)
        entry = tk.Entry(root, width=42)
        entry.grid(row=row, column=1, padx=8, pady=5)
        fields[label] = entry
    model = tk.StringVar(value="IaaS")
    tk.Label(root, text="Modelo Cloud").grid(row=5, column=0, sticky="w", padx=8, pady=5)
    tk.OptionMenu(root, model, "IaaS", "PaaS", "SaaS", "FaaS").grid(row=5, column=1, sticky="w")

    def classify():
        try:
            response = LibrarySoapClient().classify({
                "firstName": fields["Nombre"].get(), "lastName": fields["Apellidos"].get(),
                "email": fields["Correo"].get(), "isbn": fields["ISBN"].get(),
                "conceptId": fields["ID concepto"].get(), "model": model.get(),
                "clientType": "tkinter", "clientId": "classifier-gui",
            })
            messagebox.showinfo("Clasificación registrada", response.findtext(".//{*}classificationId"))
        except SoapClientError as error:
            messagebox.showerror("No se pudo clasificar", str(error))

    tk.Button(root, text="Registrar clasificación", command=classify).grid(row=6, column=1, pady=12)
    root.mainloop()


if __name__ == "__main__":
    run()
