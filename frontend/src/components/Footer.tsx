import { Search, Mail, MapPin, Phone } from "lucide-react";
import { Link } from "react-router-dom";

const Footer = () => {
  return (
    <footer className="bg-surface border-t border-border/50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary/10 rounded-xl">
                <Search className="h-5 w-5 text-primary" />
              </div>
              <span className="text-lg font-bold gradient-text">Lost & Found AI</span>
            </div>
            <p className="text-muted-foreground text-sm">
              Advanced AI matching technology helps reunite you with your belongings. 
              Report, search, and recover with confidence.
            </p>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="font-semibold text-foreground">Quick Links</h4>
            <nav className="flex flex-col space-y-2">
              <Link to="/home" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Home
              </Link>
              <Link to="/add-item" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Report Item
              </Link>
              <Link to="/profile" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Profile
              </Link>
            </nav>
          </div>

          {/* Support */}
          <div className="space-y-4">
            <h4 className="font-semibold text-foreground">Support</h4>
            <nav className="flex flex-col space-y-2">
              <a href="#" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Help Center
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary text-sm transition-colors">
                Terms of Service
              </a>
            </nav>
          </div>

          {/* Contact */}
          <div className="space-y-4">
            <h4 className="font-semibold text-foreground">Contact</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Mail className="h-4 w-4" />
                support@lostfound.ai
              </div>
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Phone className="h-4 w-4" />
                +91 9666917678
              </div>
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <MapPin className="h-4 w-4" />
                Hyderabad, TG
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-border/50 mt-8 pt-8 text-center">
          <p className="text-muted-foreground text-sm">
            © 2025 Lost & Found AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;