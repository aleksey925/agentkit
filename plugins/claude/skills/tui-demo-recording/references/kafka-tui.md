# kafka-tui - worked example

Repo: `~/CodeProjects/kafka-tui` (mounted at `/home/box/app`). A Bubble Tea TUI
for Kafka. This is the reference run behind the skill; everything here was
verified end to end.

## Launch

`connect local` auto-connects straight to the topics list (no picker). This is
not magically "stable" - the app still idle-quits in-container (see below); a
busy tape is what keeps it alive. Build, copy the binary out of the host-mounted
`dist/` (the macOS host overwrites it with a Mach-O binary mid-session, which the
container then can't exec), and run from a neutral cwd under a throwaway HOME:

```bash
make build && cp dist/kafka-tui /tmp/ktui-demo   # /tmp copy survives host rebuilds
mkdir -p /tmp/demo-home/.kafka-tui
# write clusters.yaml (below)
HOME=/tmp/demo-home  /tmp/ktui-demo connect local
```

Isolated `clusters.yaml` (3 clusters - shows colored dots + `[RO]` badge):

```yaml
# /tmp/demo-home/.kafka-tui/clusters.yaml
clusters:
  - name: local
    brokers: ['localhost:9092']
    color: green
  - name: staging
    brokers: ['localhost:9092']
    color: yellow
  - name: prod
    brokers: ['localhost:9092']
    color: red
    read_only: true
```

Colors: `red | yellow | green | gray | white`. In a VHS tape, launch by absolute
path and set `HOME`/`cd` inside a `Hide ... Show` block.

## The headless idle quit (container only)

The app idle-quits a few seconds after its last keypress in this container: a
config fsnotify watcher fails on the mounted FS and arms a delayed `tea.Quit`
(logged as "config watcher snapshot channel closed; auto-reload disabled"). It
is **not** picker-specific - `connect local` on the topics list quits on idle
too; the picker just shows it first because you sit and look at it. It is fine on
a real host. A *busy* tape (input every <=3s) records the full demo without ever
hitting it; only passive idle shots suffer.

To grab the picker as a **static PNG**, screenshot within the first couple of
seconds (before the idle quit) at a short height. One VHS command per line:

```
Set Height 340            # tight box, little empty space
Hide
... export HOME, cd, clear ...
Show
Type "/tmp/ktui-demo connect local"
Enter
Sleep 2.5s
Type ":"
Sleep 200ms
Type "clusters"
Sleep 300ms
Enter
Sleep 2s
Screenshot "/tmp/picker.png"
```

## Reaching Kafka on the host

If the broker advertises `localhost:9092`, run the forwarder and point at
`localhost`:

```bash
node scripts/tcp-forward.mjs 9092 host.docker.internal 9092 &
```

Verify a real round-trip (produce+consume), not just metadata - metadata uses
the bootstrap connection and hides the advertised-listener problem.

## Seed realistic data

Uses `franz-go` (already a dep). Write to a temp module, `go get` kgo+kadm,
`GOFLAGS=-mod=mod go run .`. Creates 5 topics with varied partitions, JSON
values with headers, and 4 consumer groups with **different lag** (one caught
up) by committing offsets behind the end via kadm:

```go
package main

import (
	"context"; "encoding/json"; "fmt"; "math/rand"; "os"; "time"
	"github.com/twmb/franz-go/pkg/kadm"; "github.com/twmb/franz-go/pkg/kgo"
)

func main() {
	rng := rand.New(rand.NewSource(42)); now := time.Now()
	customers := []string{"alice","bob","carol","dave","erin","frank","grace","heidi"}
	statuses := []string{"created","paid","shipped","delivered","cancelled"}
	currencies := []string{"USD","EUR","GBP"}; methods := []string{"card","paypal","applepay","transfer"}
	events := []string{"login","logout","page_view","add_to_cart","checkout","search"}
	products := []string{"keyboard","monitor","mouse","webcam","laptop","dock","cable"}

	type spec struct{ name string; parts int32; n int; gen func(i int) (string, any, []kgo.RecordHeader) }
	specs := []spec{
		{"orders", 6, 600, func(i int) (string, any, []kgo.RecordHeader) {
			id := fmt.Sprintf("ORD-%05d", 10000+i)
			return id, map[string]any{"order_id": id, "customer": customers[rng.Intn(len(customers))],
				"item": products[rng.Intn(len(products))], "qty": 1 + rng.Intn(5),
				"total": float64(rng.Intn(50000)) / 100, "currency": currencies[rng.Intn(len(currencies))],
				"status": statuses[rng.Intn(len(statuses))]},
				[]kgo.RecordHeader{{Key: "content-type", Value: []byte("application/json")}, {Key: "trace-id", Value: []byte(fmt.Sprintf("%08x", rng.Int31()))}}
		}},
		{"payments", 3, 400, func(i int) (string, any, []kgo.RecordHeader) {
			id := fmt.Sprintf("PAY-%05d", 20000+i)
			return id, map[string]any{"payment_id": id, "order_id": fmt.Sprintf("ORD-%05d", 10000+rng.Intn(600)),
				"amount": float64(rng.Intn(50000)) / 100, "method": methods[rng.Intn(len(methods))],
				"status": statuses[rng.Intn(len(statuses))]},
				[]kgo.RecordHeader{{Key: "source", Value: []byte("billing-svc")}}
		}},
		{"user-events", 4, 800, func(i int) (string, any, []kgo.RecordHeader) {
			u := fmt.Sprintf("user-%03d", rng.Intn(200))
			return u, map[string]any{"user_id": u, "event": events[rng.Intn(len(events))],
				"ip": fmt.Sprintf("10.%d.%d.%d", rng.Intn(255), rng.Intn(255), rng.Intn(255))}, nil
		}},
		{"clickstream", 3, 500, func(i int) (string, any, []kgo.RecordHeader) {
			s := fmt.Sprintf("sess-%06x", rng.Int31())
			return s, map[string]any{"session": s, "url": "/p/" + products[rng.Intn(len(products))], "referrer": "/search"}, nil
		}},
		{"audit-log", 1, 120, func(i int) (string, any, []kgo.RecordHeader) {
			return "", map[string]any{"actor": customers[rng.Intn(len(customers))],
				"action": []string{"create","update","delete","login"}[rng.Intn(4)], "resource": "topic/orders"}, nil
		}},
	}

	cl, err := kgo.NewClient(kgo.SeedBrokers("localhost:9092"), kgo.AllowAutoTopicCreation()); must(err)
	defer cl.Close()
	adm := kadm.NewClient(cl); ctx := context.Background()
	for _, s := range specs { adm.CreateTopics(ctx, s.parts, 1, nil, s.name) }
	time.Sleep(500 * time.Millisecond)
	for _, s := range specs {
		for i := 0; i < s.n; i++ {
			k, v, h := s.gen(i); b, _ := json.Marshal(v)
			r := &kgo.Record{Topic: s.name, Value: b, Headers: h, Timestamp: now.Add(-time.Duration(s.n-i) * time.Second)}
			if k != "" { r.Key = []byte(k) }
			cl.Produce(ctx, r, nil)
		}
		must(cl.Flush(ctx)); fmt.Println("produced", s.n, "->", s.name)
	}
	ends, err := adm.ListEndOffsets(ctx, "orders", "payments", "user-events", "clickstream"); must(err)
	groups := []struct{ name string; topics []string; lag float64 }{
		{"order-processor", []string{"orders", "payments"}, 0.18},
		{"analytics-pipeline", []string{"user-events", "clickstream"}, 0.42},
		{"fraud-detector", []string{"payments"}, 0.0},
		{"nightly-export", []string{"orders"}, 0.7},
	}
	for _, g := range groups {
		off := make(kadm.Offsets)
		ends.Each(func(o kadm.ListedOffset) {
			for _, t := range g.topics {
				if o.Topic == t {
					off.Add(kadm.Offset{Topic: o.Topic, Partition: o.Partition, At: int64(float64(o.Offset) * (1 - g.lag)), LeaderEpoch: -1})
				}
			}
		})
		_, err := adm.CommitOffsets(ctx, g.name, off); must(err); fmt.Println("group", g.name)
	}
	fmt.Println("SEED DONE")
}
func must(err error) { if err != nil { fmt.Println("ERR:", err); os.Exit(1) } }
```

## Keybinding map (verified)

Global: `:` command bar, `/` filter, `?` help, `ctrl+r` refresh-interval,
`q`/`esc` back/quit, `ctrl+c` force-quit. Command bar: `:topics`, `:groups`,
`:clusters`, `:logs`, `:config sources`, `:cluster <name>`.

- **Topics**: `j/k` move, `/` filter, `enter`/`m` browse messages, `c` topic
  configs, `g` groups for topic, `i` toggle internal, `n` new, `y` clone,
  `p` produce, `ctrl+d` delete.
- **Messages**: `enter` detail, `c` copy menu, `s` seek menu, `P` partition
  filter, `f` smart filter, `[`/`]` page, `p` produce, `R` resend.
- **Detail**: `1` JSON, `2` raw, `3` hex, `w` wrap, `c` copy, `s` save, `n`/`p`
  next/prev message, `e` $EDITOR.
- **Produce form**: `tab`/`shift+tab` fields, `enter` edit field (INSERT),
  `esc` leave, `s` send.
- **Groups**: `enter` detail, `R` reset offsets, `ctrl+d` delete. Detail:
  `tab` switch pane, `t` jump to topic messages.

Get the live keybindings from the `?` help screen or grep `internal/tui/`
(`key_dispatch.go`, per-screen `*.go`).

## Final demo.tape (verified, single session, ~36s, 1.5 MB)

`vhs demo.tape` -> `demo.gif` at 1100x540. Covers topics -> filter -> messages
-> detail (JSON/hex/copy/next) -> topic configs -> produce form -> consumer
groups + detail (lag) -> help, ending cleanly on the topics screen.

One VHS command per line (this is the format VHS actually parses; do not try to
join several with `;`):

```
Output "/tmp/demo.gif"
Set Shell "bash"
Set FontSize 12
Set Width 1100
Set Height 540
Set Padding 10
Set TypingSpeed 55ms
Set Framerate 20

Hide
Type "export HOME=/tmp/demo-home" Enter
Type "cd /tmp/demo-home" Enter
Type "clear" Enter
Show

Type "/tmp/ktui-demo connect local" Enter
Sleep 3s

# fuzzy filter
Type "/"
Sleep 350ms
Type "pay"
Sleep 1.2s
Enter
Sleep 1s
Ctrl+U
Sleep 600ms

# open orders: Up 20 clamps to top, Down 2 -> orders
Up 20
Sleep 250ms
Down 2
Sleep 600ms
Enter
Sleep 2.3s

# message detail: hex / json / copy / next
Down 3
Sleep 600ms
Enter
Sleep 1.4s
Type "3"
Sleep 1.2s
Type "1"
Sleep 800ms
Type "c"
Sleep 1.1s
Escape
Sleep 400ms
Type "n"
Sleep 600ms
Type "n"
Sleep 600ms
Escape
Sleep 500ms
Escape
Sleep 1.1s

# topic configs
Type "c"
Sleep 1.8s
Escape
Sleep 700ms

# produce form
Type "p"
Sleep 1.6s
Escape
Sleep 700ms

# consumer groups + detail (lag)
Type ":"
Sleep 250ms
Type "groups"
Sleep 350ms
Enter
Sleep 2.2s
Enter
Sleep 1.8s
Escape
Sleep 400ms
Escape
Sleep 1.1s

# help overlay, then end on a content screen (no Ctrl+C -> clean loop)
Type "?"
Sleep 2s
Escape
Sleep 1.5s
```
