package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"loginuv/client-agent/internal/auth"
	"loginuv/client-agent/internal/queue"
)

func main() {
	reader := bufio.NewReader(os.Stdin)

	fmt.Println("LoginUV Client Agent (demo)")
	fmt.Print("Codigo de usuario: ")
	userCode, _ := reader.ReadString('\n')
	fmt.Print("Contrasena: ")
	_, _ = reader.ReadString('\n')

	userCode = strings.TrimSpace(userCode)
	if userCode == "" {
		fmt.Println("Credenciales invalidas")
		return
	}

	auth.SimulateProgress(func(step auth.ProgressStep) {
		fmt.Printf("[%3d%%] %s\n", step.Percent, step.Message)
	})

	queue.Enqueue(queue.Event{Type: "LOGIN_OK"})
	fmt.Println("Sesion iniciada")
}
