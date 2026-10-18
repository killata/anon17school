import { PostForm } from "@/components/PostForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-black text-white px-4 py-3 max-w-md mx-auto selection:bg-indigo-500/30">
      <PostForm />
    </main>
  );
}
