import { useState } from "react";

import { AgentWorkbench } from "./components/AgentWorkbench";
import { WelcomeScreen } from "./components/WelcomeScreen";

export function App() {
  const [started, setStarted] = useState(false);

  if (!started) {
    return <WelcomeScreen onStart={() => setStarted(true)} />;
  }

  return <AgentWorkbench />;
}
