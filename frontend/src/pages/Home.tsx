import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
// --- Importing all necessary Lucide icons ---
import { Search, Plus, MapPin, Calendar, LogOut, Filter, Zap, Shield, MessageSquare, Globe, Cpu, UserCheck } from "lucide-react"; 
import { Link, useNavigate } from "react-router-dom";
import Masonry from "react-masonry-css";
import heroImage from "@/assets/hero-image.jpg";
import particleBg from "@/assets/particle-bg.jpg";
import Footer from "@/components/Footer";
import { useToast } from "@/hooks/use-toast";
import { formatDistanceToNow, parseISO } from 'date-fns';

// --- ITEM INTERFACE ---
interface Item {
  _id: string;
  type: 'lost' | 'found';
  title: string;
  description: string;
  category: string;
  location: string;
  date_occurred: string;
  images: string[];
  tags: string[];
  status: 'active' | 'resolved' | 'matched' | 'found'; 
  matches?: number;          
  bestMatchScore?: number;   
}
// -------------------------------------------------------------------

// --- UPDATED: FeatureCard component for side-by-side layout (requested change) ---
const FeatureCard = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
    <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        viewport={{ once: true, amount: 0.3 }}
        className="col-span-1"
    >
        <Card className="card-elegant h-full p-4">
            <CardContent className="p-0">
                <div className="flex items-start gap-4">
                    {/* Icon - Left Side */}
                    <div className="p-3 w-fit rounded-xl bg-primary/10 text-primary flex-shrink-0">
                        <Icon className="h-6 w-6" />
                    </div>
                    {/* Text - Right Side */}
                    <div>
                        <CardTitle className="text-xl mb-1 text-left">{title}</CardTitle>
                        <CardDescription className="text-left">{description}</CardDescription>
                    </div>
                </div>
            </CardContent>
        </Card>
    </motion.div>
);
// --- END UPDATED FeatureCard ---

const Home = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState({ total_items: 0, items_still_lost: 0, successful_reunions: 0 });
  const [filter, setFilter] = useState("all"); 
  const [items, setItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  useEffect(() => {
    const fetchStatsAndItems = async () => {
      setIsLoading(true);
      const token = localStorage.getItem("token");
      const headers = token ? { "Authorization": `Bearer ${token}` } : {};

      try {
        const statsResponse = await fetch("http://localhost:5000/api/items/stats", { headers });
        const itemsResponse = await fetch(`http://localhost:5000/api/items?type=${filter === 'all' ? '' : filter}&search=${searchQuery}`, { headers });

        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData);
        }

        if (itemsResponse.ok) {
          const itemsData = await itemsResponse.json();
          setItems(itemsData.items);
        }
      } catch (error: any) {
        toast({
          title: "Error fetching data",
          description: error.message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };
    fetchStatsAndItems();
  }, [filter, searchQuery, navigate, toast]);

  const breakpointColumns = {
    default: 3,
    1100: 2,
    700: 1
  };
  
  const getStatusClasses = (status: string) => {
    // ACTIVE/RESOLVED: White background, Black text
    return 'bg-white text-black border border-gray-300'; 
  }
  
  const getTypeClasses = (type: string) => {
    if (type === 'found') {
        // FOUND: Green background, White text
        return 'bg-green-500 text-white'; 
    }
    // LOST: Red background, White text
    return 'bg-red-500 text-white'; 
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation (Omitted for brevity, assumed correct) */}
      <nav className="border-b border-border/50 backdrop-blur-sm bg-background/80 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-primary/10 rounded-xl">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <span className="text-xl font-bold gradient-text">Lost & Found AI</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/add-item">
                <Button className="flex items-center gap-2" variant="default">
                  <Plus className="h-4 w-4" />
                  Report Item
                </Button>
              </Link>
              <Link to="/profile">
                <Button variant="outline">Profile</Button>
              </Link>
              <Button variant="ghost" size="sm" className="p-2" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section (Omitted for brevity, assumed correct) */}
      <section 
        className="relative py-20 hero-gradient overflow-hidden"
        style={{
          backgroundImage: `url(${particleBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundBlendMode: 'soft-light'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-background/90 to-background/70" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center lg:text-left"
            >
              <h1 className="text-4xl lg:text-6xl font-bold text-foreground mb-6">
                Find Your Lost Items with{" "}
                <span className="gradient-text">AI Power</span>
              </h1>
              <p className="text-xl text-muted-foreground mb-8 max-w-lg">
                Advanced AI matching technology helps reunite you with your belongings. 
                Report, search, and recover with confidence.
              </p>
              
              {/* Search Bar */}
              <div className="relative max-w-lg mx-auto lg:mx-0 mb-6">
                <Search className="absolute left-4 top-4 h-5 w-5 text-muted-foreground" />
                <Input
                  placeholder="Search for lost items..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 pr-4 py-4 text-lg glass-effect"
                />
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link to="/add-item">
                  <Button size="lg" className="w-full sm:w-auto">
                    <Plus className="h-5 w-5 mr-2" />
                    Report Lost Item
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-primary border-primary">
                  Browse Found Items
                </Button>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="hidden lg:block"
            >
              <img
                src={heroImage}
                alt="Lost and Found Items"
                className="w-full h-auto rounded-2xl shadow-2xl"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <Card className="card-elegant text-center">
                <CardContent className="pt-6">
                  <div className="text-3xl font-bold text-primary mb-2">
                    {stats.total_items.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">Total Items Processed</div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card className="card-elegant text-center">
                <CardContent className="pt-6">
                  {/* DISPLAY: Uses the updated stat from item_model.py which now reflects active lost items */}
                  <div className="text-3xl font-bold text-destructive mb-2">
                    {stats.items_still_lost.toLocaleString()} 
                  </div>
                  <div className="text-muted-foreground">Active Lost Items</div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <Card className="card-elegant text-center">
                <CardContent className="pt-6">
                  <div className="text-3xl font-bold text-accent mb-2">
                    {stats.successful_reunions.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">Successful Reunions</div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Recent Items */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-8"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Recent Reports</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-6">
              Browse the latest lost and found items. AI matching helps find potential matches automatically.
            </p>
            
            {/* Filter Buttons */}
            <div className="flex justify-center gap-2 mb-6">
              <Button 
                variant={filter === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter("all")}
                className="flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                All Items ({items.length})
              </Button>
              <Button 
                variant={filter === "lost" ? "destructive" : "outline"}
                size="sm"
                onClick={() => setFilter("lost")}
              >
                Lost ({items.filter(item => item.type === 'lost').length})
              </Button>
              <Button 
                variant={filter === "found" ? "secondary" : "outline"}
                size="sm"
                onClick={() => setFilter("found")}
              >
                Found ({items.filter(item => item.type === 'found').length})
              </Button>
            </div>
          </motion.div>

          <Masonry
            breakpointCols={breakpointColumns}
            className="flex w-auto gap-6"
            columnClassName="bg-clip-padding"
          >
            {items.map((item, index) => (
              <motion.div
                key={item._id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="mb-6"
              >
                <Link to={`/items/${item._id}`}>
                  <Card className="card-hover cursor-pointer">
                    <div className="relative">
                      {/* --- Image (The primary content) --- */}
                      <img
                        src={`http://localhost:5000${item.images[0]}`}
                        alt={item.title}
                        className="w-full h-48 object-cover rounded-t-lg"
                      />
                      
                      {/* 1. Item Type Badge (LOST/FOUND) - Top Left, Color, WHITE Text */}
                      <Badge
                        className={`absolute top-3 left-3 ${getTypeClasses(item.type)}`}
                      >
                        {item.type.toUpperCase()}
                      </Badge>

                      {/* 2. Status Badge (ACTIVE/RESOLVED) - Top Right, White Background, Black Text */}
                      {item.status && (
                          <Badge
                            className={`absolute top-3 right-3 ${getStatusClasses(item.status)}`}
                          >
                            {item.status.toUpperCase()}
                          </Badge>
                      )}
                      
                    </div>
                    <CardContent className="p-4">
                      {/* The "0" must be removed by structural change and final JavaScript evaluation */}
                      <CardTitle className="text-lg mb-2">{item.title}</CardTitle>
                      <CardDescription className="mb-3">
                        {item.description}
                      </CardDescription>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                        <MapPin className="h-4 w-4" />
                        {item.location}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                        <Calendar className="h-4 w-4" />
                        {formatDistanceToNow(parseISO(item.date_occurred))} ago
                      </div>
                      
                      <div className="flex justify-between items-center text-sm">
                         {/* Removed: Matches: {item.matches !== undefined ? item.matches : 0} */}
                        <div className="flex items-center gap-1 text-muted-foreground opacity-0">
                            {/* Hidden Spacer */}
                            <Zap className="h-3 w-3 text-primary" />
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {item.tags.map((tag) => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </Masonry>

          <div className="text-center mt-12">
            <Button variant="outline" size="lg">
              Load More Items
            </Button>
          </div>
        </div>
      </section>
      
      {/* --- HOW IT WORKS / FEATURES SECTION (UPDATED LAYOUT) --- */}
      <section className="py-20 bg-background">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <motion.h2 
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  viewport={{ once: true, amount: 0.5 }}
                  className="text-4xl font-bold text-foreground mb-4"
              >
                  How Our <span className="gradient-text">AI</span> Works
              </motion.h2>
              <motion.p
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  viewport={{ once: true, amount: 0.5 }}
                  className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto"
              >
                  Cutting-edge technology meets community spirit to create the most effective lost and found platform.
              </motion.p>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                  <FeatureCard 
                      icon={Cpu}
                      title="AI-Powered Matching"
                      description="Advanced computer vision and NLP algorithms analyze images, text, and descriptions to find perfect matches based on similarity scores."
                  />
                  <FeatureCard 
                      icon={MapPin}
                      title="Location Intelligence"
                      description="Smart geolocation filtering uses proximity matching (Haversine formula) to prioritize items lost or found closest to your reported location."
                  />
                  <FeatureCard 
                      icon={MessageSquare}
                      title="Secure Messaging"
                      description="A secure and anonymous channel for initial communication allows owners and finders to discuss item verification and arrange retrieval safely."
                  />
                  <FeatureCard 
                      icon={UserCheck}
                      title="Verified Community"
                      description="User verification and reputation systems (like successful reunions tracking) ensure a trusted and safe environment for item recovery."
                  />
                  <FeatureCard 
                      icon={Zap}
                      title="Instant Notifications"
                      description="Real-time alerts via email notification are sent the moment a high-confidence match is found for your reported item."
                  />
                  <FeatureCard 
                      icon={Globe}
                      title="Community Driven"
                      description="Join thousands of helpful community members—if our AI doesn't find it, our active network is actively working to reunite lost items."
                  />
              </div>
          </div>
      </section>
      {/* ---------------------------------------------------- */}
      <Footer />
    </div>
  );
};

export default Home;