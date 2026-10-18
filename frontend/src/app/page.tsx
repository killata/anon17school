import { PostForm } from "@/components/PostForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-zinc-100 px-3.5 py-2.5 max-w-md mx-auto selection:bg-zinc-800">
      <PostForm />
    </main>
  );
}
