import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, MapPin, Calendar, User, MessageCircle, Heart, Share2, Eye, Database, Clock } from "lucide-react"; 
import { Link, useParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import Map from "@/components/Map";
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { Avatar, AvatarFallback } from "@/components/ui/avatar"; 

const API_URL = "https://lostandfound-exc3.onrender.com/api";

interface UserDetails { name: string; email: string; avatar: string; rating: number; verified: boolean; }
interface Item { _id: string; type: 'lost' | 'found'; title: string; description: string; category: string; location: string; date_occurred: string; images: string[]; tags: string[]; user: UserDetails; latitude?: number | null; longitude?: number | null; views?: number; }
interface Match { id: string; candidateId: string; score: number; imageScore: number; textScore: number; locationScore: number; title: string; image: string; user: string; email: string; date_occurred?: string; }
interface GlobalStats { total_items: number; items_still_lost: number; successful_reunions: number; }

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
    if (!id) return;
    const fetchItemDetails = async () => {
      const token = localStorage.getItem("token");
      if (!token) { navigate("/"); return; }
      try {
        const [itemResponse, matchesResponse, statsResponse] = await Promise.all([
          fetch(`${API_URL}/items/${id}`, { headers: { "Authorization": `Bearer ${token}` } }),
          fetch(`${API_URL}/matches/${id}`, { headers: { "Authorization": `Bearer ${token}` } }),
          fetch(`${API_URL}/items/stats`, { headers: { "Authorization": `Bearer ${token}` } }),
        ]);

        if (!itemResponse.ok) throw new Error("Failed to fetch item data.");
        
        const itemData = await itemResponse.json();
        const matchesData = matchesResponse.ok ? await matchesResponse.json() : { matches: [] };
        const statsData = statsResponse.ok ? await statsResponse.json() : { total_items: 0, items_still_lost: 0, successful_reunions: 0 }; 

        setItem(itemData.item);
        setMatches(matchesData.matches);
        setGlobalStats(statsData); 
      } catch (err: any) {
        setError(err.message);
        toast({ title: "Error", description: err.message, variant: "destructive" });
      } finally {
        setIsLoading(false);
      }
    };
    fetchItemDetails();
  }, [id, navigate, toast]);

  const handleCopyAndContact = async (email: string, userName: string) => {
    if (!email) return;
    try {
      await navigator.clipboard.writeText(email);
      toast({
        title: "Email Copied!",
        description: `Contact ${userName} via your mail app.`,
        action: (<a href={`mailto:${email}`} className="text-primary underline">Open Mail App</a>),
      });
    } catch (err) {}
  };

  const getScoreColor = (score: number) => score * 100 >= 85 ? "text-foreground" : "text-warning";
  const getBadgeVariant = (score: number) => score * 100 >= 85 ? "secondary" : "outline";
  const getBestMatchScore = () => matches.length > 0 ? `${Math.round(matches[0].score * 100)}%` : "N/A";

  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>;
  if (error || !item) return <div className="min-h-screen flex flex-col items-center justify-center p-4 text-center"><h1 className="text-3xl font-bold mb-4 text-destructive">Error</h1><p className="text-muted-foreground">{error}</p><Link to="/home"><Button className="mt-6">Back to Home</Button></Link></div>;

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <Link to="/home" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"><ArrowLeft className="h-4 w-4" />Back to Search</Link>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="card-elegant">
              <CardContent className="p-0">
                <div className="relative">
                  {/* CRITICAL FIX: Render Cloudinary URL directly */}
                  <motion.img
                    key={currentImage}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    src={item.images && item.images.length > 0 ? item.images[currentImage] : "/static/uploads/default_avatar.jpg"}
                    alt={item.title}
                    className="w-full h-80 object-cover rounded-t-lg"
                  />
                  <Badge variant={item.type === 'lost' ? 'destructive' : 'secondary'} className="absolute top-4 left-4">{item.type.toUpperCase()}</Badge>
                </div>
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h1 className="text-2xl font-bold text-foreground mb-2">{item.title}</h1>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1"><MapPin className="h-4 w-4" />{item.location}</div>
                        <div className="flex items-center gap-1"><Calendar className="h-4 w-4" />{item.date_occurred && format(parseISO(item.date_occurred), 'PPP')}</div>
                      </div>
                    </div>
                  </div>
                  <p className="text-muted-foreground mb-6 leading-relaxed">{item.description}</p>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {item.tags.map((tag) => (<Badge key={tag} variant="outline">{tag}</Badge>))}
                  </div>
                  <Separator className="my-6" />
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-12 h-12 rounded-full border"><AvatarFallback className="bg-primary/10 text-primary"><User className="h-5 w-5" /></AvatarFallback></Avatar>
                      <div><div className="flex items-center gap-2"><span className="font-medium">{item.user.name}</span></div></div>
                    </div>
                    <Button className="flex items-center gap-2" onClick={() => handleCopyAndContact(item.user.email, item.user.name)}><MessageCircle className="h-4 w-4" />Contact</Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="card-elegant">
              <CardHeader><CardTitle className="flex items-center gap-2"><MapPin className="h-5 w-5 text-primary" />Location</CardTitle></CardHeader>
              <CardContent><Map location={item.location} latitude={item.latitude} longitude={item.longitude} /></CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="card-elegant">
              <CardHeader><CardTitle className="flex items-center gap-2"><div className="p-2 bg-primary/10 rounded-lg"><Eye className="h-5 w-5 text-primary" /></div>AI Matches</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {matches.length > 0 ? (
                  matches.map((match) => (
                    <motion.div key={match.id} className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors">
                      <div className="flex gap-3">
                        <img src={match.image} alt={match.title} className="w-16 h-16 rounded-lg object-cover" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-sm max-w-[150px] truncate">{match.title}</h4> 
                              <p className="text-xs text-muted-foreground">by {match.user}</p>
                            </div>
                            <Badge variant={getBadgeVariant(match.score)} className={getScoreColor(match.score)}>{Math.round(match.score * 100)}%</Badge>
                          </div>
                          <div className="space-y-1 mb-3">
                            <div className="flex justify-between text-xs"><span>Image Match</span><span>{Math.round(match.imageScore * 100)}%</span></div>
                            <Progress value={match.imageScore * 100} className="h-1" />
                            <div className="flex justify-between text-xs"><span>Text Match</span><span>{Math.round(match.textScore * 100)}%</span></div>
                            <Progress value={match.textScore * 100} className="h-1" />
                          </div>
                          <Link to={`/items/${match.id}`} className="w-full">
                            <Button size="sm" className="w-full" variant="outline">View Details</Button>
                          </Link>
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground"><Eye className="h-12 w-12 mx-auto mb-3 opacity-50" /><p>No matches found yet</p></div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ItemDetails;