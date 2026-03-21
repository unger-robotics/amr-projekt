import TestPanel from './TestPanel';
import type { ClientMessage } from '../types/ros';

interface ValidationPageProps {
  send: (msg: ClientMessage) => void;
}

export default function ValidationPage({ send }: ValidationPageProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-4xl mx-auto">
        <TestPanel send={send} />
      </div>
    </div>
  );
}
