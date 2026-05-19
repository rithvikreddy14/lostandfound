import { useState, useCallback } from "react"; 
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ArrowLeft, ArrowRight, Upload, MapPin, Calendar, Package, Tag, Camera } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import Map from "@/components/Map"; 

const API_URL = import.meta.env.VITE_API_URL || "https://lostandfound-exc3.onrender.com/api";

const steps = [
  { id: 1, title: "Item Type", description: "Lost or Found?" },
  { id: 2, title: "Details", description: "Title & Description" },
  { id: 3, title: "Category", description: "Category & Tags" },
  { id: 4, title: "Images", description: "Upload Photos" },
  { id: 5, title: "Location", description: "Where & When" },
];

const categories = ["Electronics", "Personal Items", "Jewelry", "Keys", "Clothing", "Documents", "Bags", "Accessories", "Sports Equipment", "Other"];

const AddItem = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({ type: "", title: "", description: "", category: "", tags: [] as string[], images: [] as File[], location: "", dateOccurred: "" });
  const [locationCoords, setLocationCoords] = useState<{ latitude: number | null, longitude: number | null }>({ latitude: null, longitude: null });
  const [tagInput, setTagInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const progress = (currentStep / steps.length) * 100;

  const nextStep = () => {
    if (currentStep === 1 && !formData.type) return;
    if (currentStep === 2 && (!formData.title || !formData.description)) return;
    if (currentStep === 3 && !formData.category) return;
    if (currentStep === 4 && formData.images.length === 0) { toast({ title: "Validation Error", description: "Please upload at least one image.", variant: "destructive" }); return; }
    if (currentStep === 5 && !formData.dateOccurred) return;
    if (currentStep < steps.length) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => { if (currentStep > 1) setCurrentStep(currentStep - 1); };

  const addTag = () => {
    if (tagInput && !formData.tags.includes(tagInput)) { setFormData({ ...formData, tags: [...formData.tags, tagInput] }); setTagInput(""); }
  };

  const removeTag = (tagToRemove: string) => { setFormData({ ...formData, tags: formData.tags.filter(tag => tag !== tagToRemove) }); };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) { const newImages = Array.from(e.target.files); setFormData({ ...formData, images: [...formData.images, ...newImages].slice(0, 5) }); }
  };
  
  const handleLocationSelect = useCallback((lat: number, lng: number) => {
    setLocationCoords({ latitude: lat, longitude: lng });
    toast({ title: "Location Selected", description: `Coordinates set to Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}` });
  }, [toast]); 

  const handleSubmit = async () => {
    if (!formData.location && (!locationCoords.latitude || !locationCoords.longitude)) { toast({ title: "Validation Error", description: "Please provide a Location Name or map point.", variant: "destructive" }); return; }
    setIsLoading(true);
    const token = localStorage.getItem("token");
    if (!token) { navigate("/"); return; }

    const form = new FormData();
    form.append("type", formData.type);
    form.append("title", formData.title);
    form.append("description", formData.description);
    form.append("category", formData.category);
    form.append("tags", JSON.stringify(formData.tags));
    form.append("location", formData.location);
    form.append("date_occurred", formData.dateOccurred);
    if (locationCoords.latitude !== null && locationCoords.longitude !== null) { form.append("latitude", String(locationCoords.latitude)); form.append("longitude", String(locationCoords.longitude)); }
    formData.images.forEach(image => { form.append("images", image); });
    
    try {
      const response = await fetch(`${API_URL}/items`, { method: "POST", headers: { "Authorization": `Bearer ${token}` }, body: form });
      if (response.ok) {
        const result = await response.json();
        toast({ title: "Item reported successfully!", description: "AI matching is now active." });
        navigate(`/items/${result.id}`); 
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to submit.");
      }
    } catch (error: any) { toast({ title: "Error", description: error.message, variant: "destructive" }); } finally { setIsLoading(false); }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1: return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
            <div className="text-center mb-8"><Package className="h-16 w-16 text-primary mx-auto mb-4" /><h2 className="text-2xl font-bold mb-2">What happened to your item?</h2></div>
            <RadioGroup value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Label htmlFor="lost" className="cursor-pointer"><Card className={`card-hover p-6 ${formData.type === 'lost' ? 'ring-2 ring-primary' : ''}`}><div className="flex items-center space-x-2"><RadioGroupItem value="lost" id="lost" /><div><div className="font-semibold text-destructive">I Lost Something</div></div></div></Card></Label>
              <Label htmlFor="found" className="cursor-pointer"><Card className={`card-hover p-6 ${formData.type === 'found' ? 'ring-2 ring-primary' : ''}`}><div className="flex items-center space-x-2"><RadioGroupItem value="found" id="found" /><div><div className="font-semibold text-accent">I Found Something</div></div></div></Card></Label>
            </RadioGroup>
          </motion.div>
        );
      case 2: return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
            <div className="space-y-2"><Label>Item Title</Label><Input placeholder="e.g., iPhone 14 Pro" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} /></div>
            <div className="space-y-2"><Label>Description</Label><Textarea placeholder="Provide detailed description..." rows={4} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} /></div>
          </motion.div>
        );
      case 3: return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
            <div className="space-y-2"><Label>Category</Label><Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}><SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger><SelectContent>{categories.map((c) => (<SelectItem key={c} value={c}>{c}</SelectItem>))}</SelectContent></Select></div>
            <div className="space-y-2"><Label>Tags</Label><div className="flex gap-2"><Input placeholder="Add tags" value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())} /><Button type="button" onClick={addTag} variant="outline"><Tag className="h-4 w-4" /></Button></div><div className="flex flex-wrap gap-2 mt-2">{formData.tags.map((tag) => (<Badge key={tag} variant="secondary" className="cursor-pointer" onClick={() => removeTag(tag)}>{tag} ×</Badge>))}</div></div>
          </motion.div>
        );
      case 4: return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
            <div className="text-center mb-6"><Camera className="h-16 w-16 text-primary mx-auto mb-4" /><h3 className="text-xl font-semibold mb-2">Upload Images</h3></div>
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center"><input type="file" multiple accept="image/*" onChange={handleImageUpload} className="hidden" id="image-upload" /><Label htmlFor="image-upload" className="cursor-pointer"><Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" /><div className="font-medium mb-2">Click to upload images</div></Label></div>
            {formData.images.length > 0 && (<div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">{formData.images.map((image, index) => (<div key={index} className="relative"><img src={URL.createObjectURL(image)} alt={`Upload ${index + 1}`} className="w-full h-24 object-cover rounded-lg" /><Button size="sm" variant="destructive" className="absolute -top-2 -right-2 h-6 w-6 p-0 rounded-full" onClick={() => { const newImages = formData.images.filter((_, i) => i !== index); setFormData({ ...formData, images: newImages }); }}>×</Button></div>))}</div>)}
          </motion.div>
        );
      case 5: return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
            <div className="space-y-2"><Label>Location Name</Label><div className="relative"><MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input placeholder="Where did this happen?" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} className="pl-10" /></div></div>
            <div className="space-y-2"><Label>Select Location on Map</Label><Card className="p-4"><Map isSelectable={true} latitude={locationCoords.latitude} longitude={locationCoords.longitude} onLocationSelect={handleLocationSelect} className="h-80" /></Card></div>
            <div className="space-y-2"><Label>When did this happen?</Label><div className="relative"><Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input type="datetime-local" required value={formData.dateOccurred} onChange={(e) => setFormData({ ...formData, dateOccurred: e.target.value })} className="pl-10" /></div></div>
          </motion.div>
        );
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8"><Link to="/home" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"><ArrowLeft className="h-4 w-4" />Back to Home</Link></div>
        <Card className="mb-8"><CardContent className="pt-6"><Progress value={progress} className="mb-4" /></CardContent></Card>
        <Card className="card-elegant">
          <CardHeader><CardTitle>{steps[currentStep - 1].title}</CardTitle></CardHeader>
          <CardContent><AnimatePresence mode="wait">{renderStepContent()}</AnimatePresence></CardContent>
        </Card>
        <div className="flex justify-between mt-8">
          <Button variant="outline" onClick={prevStep} disabled={currentStep === 1}><ArrowLeft className="h-4 w-4 mr-2" /> Previous</Button>
          {currentStep < steps.length ? (
            <Button onClick={nextStep} disabled={(currentStep === 1 && !formData.type) || (currentStep === 2 && (!formData.title || !formData.description)) || (currentStep === 3 && !formData.category) || (currentStep === 4 && formData.images.length === 0)}>Next <ArrowRight className="h-4 w-4 ml-2" /></Button>
          ) : (
            <Button onClick={handleSubmit} disabled={isLoading || (currentStep === 5 && !formData.dateOccurred)}>{isLoading ? "Submitting..." : "Submit Report"}</Button>
          )}
        </div>
      </div>
    </div>
  );
};
export default AddItem;