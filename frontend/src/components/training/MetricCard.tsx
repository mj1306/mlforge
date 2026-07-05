interface MetricCardProps {
  label: string;
  value: string;
  color: "blue" | "purple" | "indigo" | "green";
  isSelected: boolean;
  onClick: () => void;
}

const colorClasses: Record<MetricCardProps["color"], string> = {
  blue: "border-blue-500 bg-blue-50 hover:bg-blue-100",
  purple: "border-purple-500 bg-purple-50 hover:bg-purple-100",
  indigo: "border-indigo-500 bg-indigo-50 hover:bg-indigo-100",
  green: "border-green-500 bg-green-50 hover:bg-green-100",
};

const textColorClasses: Record<MetricCardProps["color"], string> = {
  blue: "text-blue-700",
  purple: "text-purple-700",
  indigo: "text-indigo-700",
  green: "text-green-700",
};

export function MetricCard({ label, value, color, isSelected, onClick }: MetricCardProps) {
  return (
    <div
      className={`rounded-lg shadow p-3 border-l-4 transition-all cursor-pointer ${colorClasses[color]} ${isSelected ? "ring-2 ring-offset-2 ring-blue-500 shadow-lg" : ""}`}
      onClick={onClick}
    >
      <div className={`text-xl font-bold ${textColorClasses[color]}`}>{value}</div>
      <div className="text-xs text-gray-600 mt-1">{label}</div>
      {label !== "Instances" && <div className="text-xs text-gray-400 mt-1">Click to view graph</div>}
    </div>
  );
}
