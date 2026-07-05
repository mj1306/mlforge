import { ArrowRight, ScanEye, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Card } from "../../components/ui";
import { ROUTES } from "../../constants/routes";

export function Home() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-8 px-6 py-12 text-center">
      <div className="space-y-3">
        <h1 className="text-4xl font-bold text-brand">MLForge</h1>
        <p className="text-gray-600 max-w-xl">
          Train computer vision models from your browser. Upload a dataset, tune hyperparameters,
          and watch training progress live -- all running locally via Docker.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl w-full">
        <Link to={ROUTES.workspace}>
          <Card className="h-full text-left hover:shadow-lg transition-shadow cursor-pointer">
            <Sparkles className="w-8 h-8 text-brand mb-3" />
            <h3 className="font-semibold text-gray-800 mb-1">Start Training</h3>
            <p className="text-sm text-gray-600">
              Pick a model, upload a dataset, and train it end-to-end.
            </p>
            <span className="inline-flex items-center gap-1 text-sm text-brand mt-3 font-medium">
              Open workspace <ArrowRight className="w-4 h-4" />
            </span>
          </Card>
        </Link>

        <Link to={ROUTES.annotation}>
          <Card className="h-full text-left hover:shadow-lg transition-shadow cursor-pointer">
            <ScanEye className="w-8 h-8 text-brand-secondary mb-3" />
            <h3 className="font-semibold text-gray-800 mb-1">Annotate Data</h3>
            <p className="text-sm text-gray-600">
              Launch a local CVAT instance to label images before training.
            </p>
            <span className="inline-flex items-center gap-1 text-sm text-brand-secondary mt-3 font-medium">
              Open annotation <ArrowRight className="w-4 h-4" />
            </span>
          </Card>
        </Link>
      </div>
    </div>
  );
}
