"use client";

import { useState } from "react";

type Msg = {
  role: "user" | "bot";
  text: string;
};

function Home() {
  const[file,setFile]=useState<File | null>(null)
  const[upload, setUpload]=useState("");


  async function upload_file() {
      if(!file) return;

      const data= new FormData()
      data.append("file", file)
      const res=await fetch("http://127.0.0.1:8000/upload",{
        method:"POST",
        body:data,
      });
      const info=await res.json();
      setUpload(info.message || info.detail)

  }
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "bot",
      text: "Hi! I am your AI assistant. Ask me anything.",
    },
  ]);

  const [inp, setInp] = useState("");

  async function sendMsg() {
    if (inp.length==0) return;

    const userMsg: Msg = {
      role: "user",
      text: inp,
    };

    // const botMsg: Msg = {
    //   role: "bot",
    //   text: "This is a demo reply. Later we will connect real AI here.",
    // };
    
    setMsgs((initial) => [...initial, userMsg]);
    setInp("");

    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: inp,
      }),
    });
  
    const data = await res.json();
    const botMsg: Msg = {
      role: "bot",
      text: data.reply,
    };
  
    setMsgs((old) => [...old, botMsg]);
  }

  return (
    <main className="min-h-screen flex justify-center bg-yellow-300">
      <div className="w-full max-w-7xl bg-amber-500 flex flex-col min-h-screen">
        <header className="border-b p-5 flex flex-col">
          <h1 className="text-xl font-semibold">RAG Chatbot</h1>
          <p className="text-sm text-gray-500">
            Simple chat UI — backend will come later
          </p>
        </header>

        <section className="flex-1 p-4 space-y-3 overflow-y-auto">
          {msgs.map((m, i) => (
            <div
              key={i}
              className={`flex ${
                m.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2 text-xl ${
                  m.role === "user"
                    ? "bg-black text-green-600"
                    : "bg-gray-200 text-black"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </section>

        <footer className="border-t p-4 flex gap-2 text-blue-700">
          <div className="border-t-amber-50 p-4">
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
              }}
            />

            <button
              onClick={upload_file}
              className="ml-2 bg-black text-white px-4 py-2 rounded-xl"
            >
              Upload
            </button>

            {upload && (
              <p className="text-sm text-gray-500 mt-2">{upload}</p>
            )}
          </div>
          <input
            value={inp}
            onChange={(e) => setInp(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMsg();
            }}
            placeholder="Type your message..."
            className="flex-1 border rounded-xl px-4 py-2 outline-none focus:ring-2 focus:ring-black"
          />

          <button
            onClick={sendMsg}
            className="bg-black text-gray px-5 py-2 rounded-b-full text-white"
          >
            Send
          </button>
        </footer>
      </div>
    </main>
  );
}
export default Home;