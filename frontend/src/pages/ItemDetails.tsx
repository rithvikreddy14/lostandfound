import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
// Imported Database icon for the Total Items Processed metric
import { ArrowLeft, MapPin, Calendar, User, MessageCircle, Heart, Share2, Eye, Star, Database, Clock } from "lucide-react"; 
import { Link, useParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import Map from "@/components/Map";
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { Avatar, AvatarFallback } from "@/components/ui/avatar"; 

// Define the types for the data you expect from the backend
interface UserDetails {
  name: string;
  email: string;
  avatar: string;
  rating: number;
  verified: boolean;
}

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
  user: UserDetails;
  latitude?: number | null;
  longitude?: number | null;
  views?: number; 
}

interface Match {
  id: string;
  candidateId: string;
  score: number;
  imageScore: number;
  textScore: number;
  locationScore: number;
  title: string;
  image: string;
  user: string;
  email: string;
  date_occurred?: string; // Added date_occurred for match item
}

// State for global stats
interface GlobalStats {
    total_items: number;
    items_still_lost: number;
    successful_reunions: number;
}

const ItemDetails = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<Item | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [globalStats, setGlobalStats] = useState<GlobalStats>({ total_items: 0, items_still_lost: 0, successful_reunions: 0 }); 
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentImage, setCurrentImage] = useState(0);
  const { toast } = useToast();

  useEffect(() => {
    if (!id) {
      setError("Item ID not found in URL.");
      setIsLoading(false);
      return;
    }

    const fetchItemDetails = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/");
        return;
      }
      try {
        // Fetch item details, match results, and global stats concurrently
        const [itemResponse, matchesResponse, statsResponse] = await Promise.all([
          fetch(`http://localhost:5000/api/items/${id}`, {
            headers: { "Authorization": `Bearer ${token}` },
          }),
          fetch(`http://localhost:5000/api/matches/${id}`, {
            headers: { "Authorization": `Bearer ${token}` },
          }),
          fetch(`http://localhost:5000/api/items/stats`, { 
            headers: { "Authorization": `Bearer ${token}` },
          }),
        ]);

        if (!itemResponse.ok) {
          throw new Error("Failed to fetch item data.");
        }
        
        const itemData = await itemResponse.json();
        const matchesData = matchesResponse.ok ? await matchesResponse.json() : { matches: [] };
        const statsData = statsResponse.ok ? await statsResponse.json() : { total_items: 0, items_still_lost: 0, successful_reunions: 0 }; 

        setItem(itemData.item);
        setMatches(matchesData.matches);
        setGlobalStats(statsData); 

      } catch (err: any) {
        setError(err.message);
        toast({
          title: "Error",
          description: err.message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchItemDetails();
  }, [id, navigate, toast]);

  // NEW: Handle Copy Email and Toast Notification
  const handleCopyAndContact = async (email: string, userName: string) => {
    if (!email) {
      toast({
        title: "Contact Error",
        description: "User contact information is not available.",
        variant: "destructive",
      });
      return;
    }
    
    try {
      await navigator.clipboard.writeText(email);
      toast({
        title: "Email Copied!",
        description: `The email address of ${userName} has been copied. Click 'Contact' to open your mail app or paste the address into a new email.`,
        action: (
          <a href={`mailto:${email}`} className="text-primary hover:text-primary-dark font-medium underline">
             Open Mail App
          </a>
        ),
      });
    } catch (err) {
      toast({
        title: "Copy Failed",
        description: "Please manually copy the email or check browser permissions.",
        variant: "default",
      });
    }
  };


  const getScoreColor = (score: number) => {
    const percentage = score * 100;
    
    if (percentage >= 85) return "text-foreground"; 
    if (percentage >= 70) return "text-warning";
    return "text-muted-foreground";
  };
  
  const getBadgeVariant = (score: number) => {
    const percentage = score * 100;

    if (percentage >= 85) return "secondary"; 
    if (percentage >= 70) return "outline";
    return "outline";
  }

  const getBestMatchScore = () => {
    return matches.length > 0 ? `${Math.round(matches[0].score * 100)}%` : "N/A";
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4 text-center">
        <h1 className="text-3xl font-bold mb-4 text-destructive">Error</h1>
        <p className="text-muted-foreground">{error || "Item not found."}</p>
        <Link to="/home">
          <Button className="mt-6">Back to Home</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/home" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4">
            <ArrowLeft className="h-4 w-4" />
            Back to Search
          </Link>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Item Info */}
            <Card className="card-elegant">
              <CardContent className="p-0">
                {/* Image Gallery */}
                <div className="relative">
                  <motion.img
                    key={currentImage}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                    src={`http://localhost:5000${item.images[currentImage]}`}
                    alt={item.title}
                    className="w-full h-80 object-cover rounded-t-lg"
                  />
                  <Badge
                    variant={item.type === 'lost' ? 'destructive' : 'secondary'}
                    className="absolute top-4 left-4"
                  >
                    {item.type.toUpperCase()}
                  </Badge>

                  {/* Image Navigation */}
                  {item.images.length > 1 && (
                    <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
                      {item.images.map((_, index) => (
                        <button
                          key={index}
                          onClick={() => setCurrentImage(index)}
                          className={`w-3 h-3 rounded-full transition-all ${
                            index === currentImage ? 'bg-white' : 'bg-white/50'
                          }`}
                        />
                      ))}
                    </div>
                  )}
                </div>

                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h1 className="text-2xl font-bold text-foreground mb-2">{item.title}</h1>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" />
                          {item.location}
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {format(parseISO(item.date_occurred), 'PPP')}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Heart className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Share2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <p className="text-muted-foreground mb-6 leading-relaxed">
                    {item.description}
                  </p>

                  <div className="flex flex-wrap gap-2 mb-6">
                    {item.tags.map((tag) => (
                      <Badge key={tag} variant="outline">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  <Separator className="my-6" />

                  {/* User Info */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-12 h-12 rounded-full border">
                          <AvatarFallback className="bg-primary/10 text-primary">
                            <User className="h-5 w-5" />
                          </AvatarFallback>
                      </Avatar>
                      
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{item.user.name}</span>
                          {item.user.verified && (
                            <Badge variant="secondary" className="text-xs">
                              Verified
                            </Badge>
                          )}
                        </div>
                        {/* REMOVED: User rating display was here */}
                      </div>
                    </div>

                    {/* FIXED: Changed button action to Copy Email and display Toast */}
                    <Button 
                      className="flex items-center gap-2" 
                      onClick={() => handleCopyAndContact(item.user.email, item.user.name)}
                    >
                      <MessageCircle className="h-4 w-4" />
                      Contact
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Map Section */}
            <Card className="card-elegant">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-primary" />
                  Location
                </CardTitle>
                <CardDescription>
                  Item location: {item.location}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Map location={item.location} latitude={item.latitude} longitude={item.longitude} />
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Dynamic AI Matches */}
          <div className="space-y-6">
            <Card className="card-elegant">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Eye className="h-5 w-5 text-primary" />
                  </div>
                  AI Matches
                </CardTitle>
                <CardDescription>
                  AI found {matches.length} potential matches
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {matches.length > 0 ? (
                  matches.map((match) => (
                    <motion.div
                      key={match.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex gap-3">
                        <img
                          src={`http://localhost:5000${match.image}`}
                          alt={match.title}
                          className="w-16 h-16 rounded-lg object-cover"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                                {/* 1. FIXED: Added max-w-[150px] and truncate class for title overflow */}
                              <h4 className="font-medium text-sm max-w-[150px] truncate">{match.title}</h4> 
                              <p className="text-xs text-muted-foreground">by {match.user}</p>
                              {/* UX SUGGESTION: Added match item date for better context */}
                              {match.date_occurred && (
                                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                    <Clock className="h-3 w-3" />
                                    {formatDistanceToNow(parseISO(match.date_occurred))} ago
                                </p>
                              )}
                            </div>
                            <Badge
                              variant={getBadgeVariant(match.score)}
                              className={getScoreColor(match.score)}
                            >
                              {Math.round(match.score * 100)}%
                            </Badge>
                          </div>

                          <div className="space-y-1 mb-3">
                            {/* AI Match Scores - Dynamic Progress Bars */}
                            <div className="flex justify-between text-xs">
                              <span>Image Match</span>
                              <span>{Math.round(match.imageScore * 100)}%</span>
                            </div>
                            <Progress value={match.imageScore * 100} className="h-1" />

                            <div className="flex justify-between text-xs">
                              <span>Text Match</span>
                              <span>{Math.round(match.textScore * 100)}%</span>
                            </div>
                            <Progress value={match.textScore * 100} className="h-1" />

                            <div className="flex justify-between text-xs">
                              <span>Location</span>
                              <span>{Math.round(match.locationScore * 100)}%</span>
                            </div>
                            <Progress value={match.locationScore * 100} className="h-1" />
                          </div>

                          {/* Action Button */}
                          <Link to={`/items/${match.id}`} className="w-full">
                            <Button
                              size="sm"
                              className="w-full"
                              variant="outline"
                            >
                              View Match Details
                            </Button>
                          </Link>

                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Eye className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No matches found yet</p>
                    <p className="text-sm">AI is still analyzing...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card className="card-elegant">
              <CardContent className="pt-6">
                <div className="text-center space-y-2">
                  <div className="text-2xl font-bold text-primary">
                    {getBestMatchScore()}
                  </div>
                  <div className="text-sm text-muted-foreground">Best Match Score</div>
                </div>
                <Separator className="my-4" />
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    {/* Replaced "Views" with "Total Database Items" (Social Proof) */}
                    <div className="text-lg font-semibold flex items-center justify-center gap-1">
                      <Database className="h-4 w-4 text-primary" />
                      {globalStats.total_items}
                    </div> 
                    <div className="text-xs text-muted-foreground">Items Processed</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">{matches.length}</div> 
                    <div className="text-xs text-muted-foreground">Matches Found</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ItemDetails;