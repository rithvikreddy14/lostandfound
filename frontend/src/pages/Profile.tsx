import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ArrowLeft, User, Mail, Phone, Edit, Trash2, MapPin, Calendar, Trophy, TrendingUp, CheckCircle, XCircle } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import Masonry from "react-masonry-css";
import { format, parseISO } from 'date-fns';
import { AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog"; 

const API_URL = "https://lostandfound-exc3.onrender.com/api";

interface UserData { _id: string; name: string; email: string; phone?: string; avatar?: string; joinDate?: string; verified?: boolean; stats: { totalItems: number; lostItems: number; foundItems: number; successfulMatches: number; helpedOthers: number; }; }
interface Item { _id: string; type: 'lost' | 'found'; title: string; description: string; category: string; location: string; date_occurred: string; status: 'active' | 'matched' | 'found' | 'resolved'; images: string[]; views: number; matches: number; }

const Profile = () => {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [userItems, setUserItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isResolutionDialogOpen, setIsResolutionDialogOpen] = useState(false);
  const [itemToResolve, setItemToResolve] = useState<Item | null>(null);
  const { toast } = useToast();

  const fetchUserProfile = async () => {
    const token = localStorage.getItem("token");
    if (!token) { navigate("/"); return; }
    setIsLoading(true);
    try {
      const userResponse = await fetch(`${API_URL}/users/me`, { headers: { "Authorization": `Bearer ${token}` } });
      const itemsResponse = await fetch(`${API_URL}/items?user_id=me`, { headers: { "Authorization": `Bearer ${token}` } });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUserData(userData.user);
      }
      if (itemsResponse.ok) {
        const itemsData = await itemsResponse.json();
        setUserItems(itemsData.items); 
      }
    } catch (error: any) {
      if (error.message.includes("401")) navigate("/");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchUserProfile(); }, [navigate, toast]);

  const handleResolveItem = (item: Item) => { setItemToResolve(item); setIsResolutionDialogOpen(true); };

  const finalizeResolution = async (resolutionType: 'resolved' | 'deleted') => {
    if (!itemToResolve) return;
    const token = localStorage.getItem("token");
    const method = resolutionType === 'resolved' ? "PUT" : "DELETE";
    setIsResolutionDialogOpen(false);
    
    try {
      const response = await fetch(`${API_URL}/items/${itemToResolve._id}`, {
        method: method,
        headers: { "Authorization": `Bearer ${token}`, ...(method === 'PUT' && { 'Content-Type': 'application/json' }) },
        body: resolutionType === 'resolved' ? JSON.stringify({ status: 'resolved' }) : undefined,
      });

      if (response.ok) {
        fetchUserProfile(); 
        toast({ title: resolutionType === 'resolved' ? "Reunion Recorded!" : "Item Deleted" });
      }
    } catch (error: any) { toast({ title: "Error", description: error.message, variant: "destructive" }); }
  };

  const getStatusColor = (status: string) => status === 'resolved' ? 'bg-accent/20 text-accent' : 'bg-blue-100 text-blue-800';

  if (isLoading || !userData) return <div className="min-h-screen flex items-center justify-center"><motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>;

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8"><Link to="/home" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"><ArrowLeft className="h-4 w-4" />Back to Home</Link></div>
        <div className="grid lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1">
            <Card className="card-elegant sticky top-8">
              <CardContent className="pt-6">
                <div className="text-center space-y-4">
                  <Avatar className="h-24 w-24 mx-auto"><AvatarFallback className="text-4xl bg-primary/10 text-primary">{userData.name.split(' ').map(n => n[0]).join('')}</AvatarFallback></Avatar>
                  <div><h2 className="text-xl font-bold text-foreground">{userData.name}</h2></div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Tabs defaultValue="items" className="space-y-6">
              <TabsList className="grid w-full grid-cols-3"><TabsTrigger value="items">My Items</TabsTrigger><TabsTrigger value="stats">Statistics</TabsTrigger></TabsList>
              <TabsContent value="items" className="space-y-6">
                <Masonry breakpointCols={{default: 2, 700: 1}} className="flex w-auto gap-6" columnClassName="bg-clip-padding">
                  {userItems.map((item, index) => (
                    <motion.div key={item._id} className="mb-6">
                      <Card className="card-hover">
                        <div className="relative">
                          {/* CRITICAL FIX: Render Cloudinary URL directly */}
                          <img src={item.images && item.images.length > 0 ? item.images[0] : "/static/uploads/default_avatar.jpg"} alt={item.title} className="w-full h-48 object-cover rounded-t-lg" />
                          <div className="absolute top-3 left-3 flex gap-2"><Badge variant={item.type === 'lost' ? 'destructive' : 'secondary'}>{item.type.toUpperCase()}</Badge></div>
                          <div className="absolute top-3 right-3 flex gap-2">
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 bg-background/80 hover:bg-destructive/80 transition-colors" onClick={(e) => { e.preventDefault(); handleResolveItem(item); }} disabled={item.status === 'resolved'}><Trash2 className="h-4 w-4" /></Button>
                          </div>
                        </div>
                        <CardContent className="p-4">
                          <CardTitle className="text-lg mb-2">{item.title}</CardTitle>
                          <Link to={`/items/${item._id}`}><Button variant="outline" size="sm">View Details</Button></Link>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </Masonry>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
      
      <AlertDialog open={isResolutionDialogOpen} onOpenChange={setIsResolutionDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Resolve or Delete</AlertDialogTitle><AlertDialogDescription>Confirm status.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setItemToResolve(null)}>Cancel</AlertDialogCancel>
            <Button variant="default" onClick={() => finalizeResolution('resolved')}><CheckCircle className="h-4 w-4 mr-2"/> Mark as Resolved</Button>
            <Button variant="destructive" onClick={() => finalizeResolution('deleted')}><XCircle className="h-4 w-4 mr-2"/> Delete Permanently</Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
export default Profile;