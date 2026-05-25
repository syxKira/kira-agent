type WelcomeScreenProps = {
  onStart: () => void;
};

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  return (
    <main className="welcome-shell">
      <div className="welcome-glow welcome-glow-one" aria-hidden="true" />
      <div className="welcome-glow welcome-glow-two" aria-hidden="true" />
      <section className="welcome-panel">
        <div className="welcome-copy-block">
          <p className="eyebrow">Kira Agent</p>
          <h1>
            Kira
            <span> Agent</span>
          </h1>
          <p className="welcome-copy">
            一个专业的数据agent助手，帮你把复杂数据任务拆成清晰行动。
          </p>
        </div>

        <article className="agent-card" aria-label="Kira agent">
          <div className="agent-card-header">
            <span className="agent-avatar" aria-hidden="true">
              K
            </span>
            <div>
              <h2>Kira</h2>
              <p>一个专业的数据agent助手</p>
            </div>
          </div>
          <div className="agent-card-beam" aria-hidden="true" />
        </article>

        <button className="primary-button" type="button" onClick={onStart}>
          立刻开始
        </button>
      </section>
    </main>
  );
}
