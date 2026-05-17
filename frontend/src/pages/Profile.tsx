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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"; // Assuming this ShadCN component path is correct

interface UserData {
  _id: string;
  name: string;
  email: string;
  phone?: string;
  avatar?: string;
  joinDate?: string;
  verified?: boolean;
  stats: {
    totalItems: number;
    lostItems: number;
    foundItems: number;
    successfulMatches: number;
    helpedOthers: number;
  };
}

interface Item {
  _id: string;
  type: 'lost' | 'found';
  title: string;
  description: string;
  category: string;
  location: string;
  date_occurred: string;
  status: 'active' | 'matched' | 'found' | 'resolved';
  images: string[];
  views: number;
  matches: number;
}

const Profile = () => {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [userItems, setUserItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // NEW STATE: For handling the resolution dialog
  const [isResolutionDialogOpen, setIsResolutionDialogOpen] = useState(false);
  const [itemToResolve, setItemToResolve] = useState<Item | null>(null);

  const { toast } = useToast();

  const fetchUserProfile = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/");
      return;
    }
    setIsLoading(true);
    try {
      // 1. Fetch authenticated user data (user profile and stats)
      const userResponse = await fetch("http://localhost:5000/api/users/me", {
        headers: { "Authorization": `Bearer ${token}` }, // <-- AUTHENTICATED
      });
      
      // 2. Fetch items belonging ONLY to this user (user_id=me)
      const itemsResponse = await fetch("http://localhost:5000/api/items?user_id=me", {
        headers: { "Authorization": `Bearer ${token}` }, // <-- AUTHENTICATED
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUserData(userData.user);
      } else {
        throw new Error("Failed to fetch user profile.");
      }

      if (itemsResponse.ok) {
        const itemsData = await itemsResponse.json();
        setUserItems(itemsData.items); // Render dynamic, user-specific items
      }
      
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
      // If profile fails to load (e.g., token expired), redirect to login
      if (error.message.includes("401")) {
         navigate("/");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUserProfile();
  }, [navigate, toast]);


  const handleSave = async () => {
    if (!userData) return;
    setIsEditing(false); // Optimistically close edit mode
    const token = localStorage.getItem("token");

    try {
      const response = await fetch("http://localhost:5000/api/users/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: userData.name,
          phone: userData.phone,
        }),
      });

      if (response.ok) {
        const updatedData = await response.json();
        setUserData(updatedData.user);
        setIsEditing(false);
        toast({
          title: "Profile updated!",
          description: "Your profile information has been saved successfully.",
        });
      } else {
        throw new Error("Failed to save profile changes.");
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // --- NEW: Function to handle resolution of an item ---
  const handleResolveItem = (item: Item) => {
    setItemToResolve(item);
    setIsResolutionDialogOpen(true);
  };

  const finalizeResolution = async (resolutionType: 'resolved' | 'deleted') => {
    if (!itemToResolve) return;
    
    const itemId = itemToResolve._id;
    const token = localStorage.getItem("token");
    const method = resolutionType === 'resolved' ? "PUT" : "DELETE";
    const endpoint = `http://localhost:5000/api/items/${itemId}`;
    const body = resolutionType === 'resolved' ? JSON.stringify({ status: 'resolved' }) : undefined;

    setIsResolutionDialogOpen(false);
    
    try {
      const response = await fetch(endpoint, {
        method: method,
        headers: { 
            "Authorization": `Bearer ${token}`,
            ...(method === 'PUT' && { 'Content-Type': 'application/json' })
        },
        body: body,
      });

      if (response.ok) {
        // Refresh items and stats to show new state
        fetchUserProfile(); 
        
        toast({
          title: resolutionType === 'resolved' ? "Reunion Recorded!" : "Item Deleted",
          description: resolutionType === 'resolved' 
            ? "Congratulations! Your successful reunion has been recorded."
            : "Your item has been removed from the platform.",
          variant: resolutionType === 'resolved' ? "default" : "destructive",
        });
      } else {
        throw new Error(`Failed to ${resolutionType} item.`);
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setItemToResolve(null);
    }
  };
  // --- END NEW RESOLUTION LOGIC ---


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-blue-100 text-blue-800';
      case 'matched': return 'bg-yellow-100 text-yellow-800';
      case 'found': return 'bg-green-100 text-green-800';
      case 'resolved': return 'bg-accent/20 text-accent'; // Highlight successful resolution
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const breakpointColumns = {
    default: 2,
    700: 1
  };

  if (isLoading || !userData) {
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

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/home" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4">
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Link>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <Card className="card-elegant sticky top-8">
              <CardContent className="pt-6">
                <div className="text-center space-y-4">
                  <Avatar className="h-24 w-24 mx-auto">
                    <AvatarFallback className="text-4xl bg-primary/10 text-primary">
                      {userData.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div>
                    <h2 className="text-xl font-bold text-foreground">{userData.name}</h2>
                    <p className="text-muted-foreground">Member since {userData.joinDate || 'N/A'}</p>
                    {userData.verified && (
                      <Badge variant="secondary" className="mt-2">
                        Verified
                      </Badge>
                    )}
                    {/* Removed: User rating display */}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{userData.stats.totalItems}</div>
                      <div className="text-xs text-muted-foreground">Total Reports</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-accent">{userData.stats.successfulMatches}</div>
                      <div className="text-xs text-muted-foreground">Reunions</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Tabs defaultValue="items" className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="items">My Items</TabsTrigger>
                <TabsTrigger value="profile">Profile</TabsTrigger>
                <TabsTrigger value="stats">Statistics</TabsTrigger>
              </TabsList>

              {/* My Items Tab - Displays ONLY User's Items */}
              <TabsContent value="items" className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-2xl font-bold">My Items</h3>
                  <Link to="/add-item">
                    <Button>Add New Item</Button>
                  </Link>
                </div>

                <Masonry
                  breakpointCols={breakpointColumns}
                  className="flex w-auto gap-6"
                  columnClassName="bg-clip-padding"
                >
                  {userItems.map((item, index) => (
                    <motion.div
                      key={item._id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, delay: index * 0.1 }}
                      className="mb-6"
                    >
                      <Card className="card-hover">
                        <div className="relative">
                          <img
                            src={`http://localhost:5000${item.images[0]}`}
                            alt={item.title}
                            className="w-full h-48 object-cover rounded-t-lg"
                          />
                          <div className="absolute top-3 left-3 flex gap-2">
                            <Badge variant={item.type === 'lost' ? 'destructive' : 'secondary'}>
                              {item.type.toUpperCase()}
                            </Badge>
                            <Badge className={getStatusColor(item.status)}>
                              {item.status}
                            </Badge>
                          </div>
                          <div className="absolute top-3 right-3 flex gap-2">
                            {/* Option 1: Edit button (Placeholder) */}
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 bg-background/80">
                              <Edit className="h-4 w-4" />
                            </Button>
                            
                            {/* Option 2: Resolve/Delete Button (Triggers Modal) */}
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className={`h-8 w-8 p-0 bg-background/80 hover:bg-destructive/80 transition-colors ${item.status === 'resolved' ? 'opacity-50 cursor-default' : ''}`}
                              onClick={(e) => {
                                  e.preventDefault();
                                  handleResolveItem(item); // Triggers the custom resolution flow
                              }}
                              disabled={item.status === 'resolved'}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <CardContent className="p-4">
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
                            {format(parseISO(item.date_occurred), 'PPP')}
                          </div>
                          <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-3">
                              {/* Removed: Matches: {item.matches || 0} */}
                            </div>
                            <Link to={`/items/${item._id}`}>
                              <Button variant="outline" size="sm">
                                View Details
                              </Button>
                            </Link>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </Masonry>
              </TabsContent>

              {/* Profile Tab */}
              <TabsContent value="profile" className="space-y-6">
                <Card className="card-elegant">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle>Profile Information</CardTitle>
                        <CardDescription>Manage your account details</CardDescription>
                      </div>
                      <Button
                        variant={isEditing ? "default" : "outline"}
                        onClick={isEditing ? handleSave : () => setIsEditing(true)}
                      >
                        {isEditing ? "Save Changes" : "Edit Profile"}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="name"
                          value={userData?.name || ''}
                          onChange={(e) => setUserData({ ...userData!, name: e.target.value })}
                          disabled={!isEditing}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="email"
                          type="email"
                          value={userData?.email || ''}
                          disabled
                          className="pl-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="phone"
                          type="tel"
                          value={userData?.phone || ''}
                          onChange={(e) => setUserData({ ...userData!, phone: e.target.value })}
                          disabled={!isEditing}
                          className="pl-10"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Statistics Tab */}
              <TabsContent value="stats" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <Card className="card-elegant">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <Trophy className="h-8 w-8 text-primary mx-auto mb-2" />
                        <div className="text-2xl font-bold text-primary">{userData?.stats.successfulMatches || 0}</div>
                        <div className="text-xs text-muted-foreground">Successful Reunions</div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="card-elegant">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <TrendingUp className="h-8 w-8 text-accent mx-auto mb-2" />
                        <div className="text-2xl font-bold text-accent">{userData?.stats.helpedOthers || 0}</div>
                        <div className="text-xs text-muted-foreground">People Helped</div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Card className="card-elegant">
                  <CardHeader>
                    <CardTitle>Activity Overview</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-destructive">{userData?.stats.lostItems || 0}</div>
                        <div className="text-sm text-muted-foreground">Lost Items</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-secondary-foreground">{userData?.stats.foundItems || 0}</div>
                        <div className="text-sm text-muted-foreground">Found Items</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-primary">{userData?.stats.totalItems || 0}</div>
                        <div className="text-sm text-muted-foreground">Total Reports</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-accent">{userData?.stats.successfulMatches || 0}</div>
                        <div className="text-sm text-muted-foreground">Success Rate</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
      
      {/* --- Resolution/Deletion Modal (AlertDialog) --- */}
      <AlertDialog open={isResolutionDialogOpen} onOpenChange={setIsResolutionDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Resolve or Delete "{itemToResolve?.title}"</AlertDialogTitle>
            <AlertDialogDescription>
              Please confirm the status of this report. If the item was successfully reunited, choose "Resolved" to update your stats. Otherwise, choose "Delete Permanently".
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setItemToResolve(null)}>Cancel</AlertDialogCancel>
            
            {/* Resolution Option */}
            <Button 
                variant="default" 
                onClick={() => finalizeResolution('resolved')}
                className="flex items-center gap-2"
                disabled={itemToResolve?.status === 'resolved'}
            >
                <CheckCircle className="h-4 w-4" />
                Mark as Resolved
            </Button>
            
            {/* Deletion Option */}
            <Button 
                variant="destructive" 
                onClick={() => finalizeResolution('deleted')}
                className="flex items-center gap-2"
            >
                <XCircle className="h-4 w-4" />
                Delete Permanently
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      {/* ----------------------------------------------- */}
    </div>
  );
};

export default Profile;