import { ThemeProvider } from "./context/ThemeContext";
import { NavBar, DashboardGrid } from "./components/dashboard";

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-secondary-50 dark:bg-secondary-900 transition-colors duration-300">
        {/* Subtle background gradient */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200/30 dark:bg-primary-700/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-primary-300/20 dark:bg-primary-800/10 rounded-full blur-3xl" />
        </div>

        {/* Main content */}
        <div className="relative z-10">
          <NavBar />
          <main>
            <DashboardGrid />
          </main>

          {/* Footer */}
          <footer className="py-6 text-center">
            <p className="text-xs text-secondary-400">
              © 2024 Mevolut Energy Dashboard • Sustainable Living
            </p>
          </footer>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;
