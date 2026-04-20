const [state, setState] = useState("idle");
const [text, setText] = useState("");

useEffect(() => {
  const ws = new WebSocket("ws://localhost:8000/ui-stream");

  ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);

    if (data.type === "listening") setState("listening");
    if (data.type === "processing") {
      setState("processing");
      setText(data.text);
    }
    if (data.type === "response") {
      setState("speaking");
      setText(data.text);
    }
    if (data.type === "idle") setState("idle");
  };

  return () => ws.close();
}, []);

{state === "listening" && (
  <div className="flex space-x-1 items-end h-12">
    {[...Array(20)].map((_, i) => (
      <div
        key={i}
        className="w-1 bg-green-400 animate-pulse"
        style={{
          height: `${Math.random() * 40 + 10}px`,
          animationDelay: `${i * 0.05}s`
        }}
      />
    ))}
  </div>
)}

<div className="mt-6 text-center">

  {state === "processing" && (
    <div className="animate-pulse text-yellow-400">
      🧠 Understanding: "{text}"
    </div>
  )}

  {state === "speaking" && (
    <div className="animate-fadeIn text-green-400">
      🔊 {text}
    </div>
  )}

</div>