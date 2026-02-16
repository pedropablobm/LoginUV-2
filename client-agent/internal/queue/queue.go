package queue

import "fmt"

type Event struct {
	Type      string
	Payload   map[string]string
	CreatedAt string
}

// TODO: Replace with SQLite persistence.
func Enqueue(e Event) {
	fmt.Printf("queued event: %s\n", e.Type)
}
