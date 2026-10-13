// The 3 models and their honest score (tested on tools never seen in training)
export default function ModelCards({ models }) {
  return (
    <div className="card">
      <h2>Models</h2>
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Task</th>
            <th>Score (leave-one-tool-out)</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.task}>
              <td>{m.name}</td>
              <td>{m.task}</td>
              <td>{m.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
