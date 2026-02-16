package auth

import "time"

type ProgressStep struct {
	Percent int
	Message string
}

func LoginProgressSteps() []ProgressStep {
	return []ProgressStep{
		{Percent: 20, Message: "Validando datos locales"},
		{Percent: 45, Message: "Conectando al servidor"},
		{Percent: 70, Message: "Validando credenciales"},
		{Percent: 90, Message: "Aplicando politicas de sesion"},
		{Percent: 100, Message: "Acceso concedido"},
	}
}

func SimulateProgress(cb func(ProgressStep)) {
	for _, step := range LoginProgressSteps() {
		cb(step)
		time.Sleep(350 * time.Millisecond)
	}
}
