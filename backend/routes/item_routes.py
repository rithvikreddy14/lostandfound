from flask import Blueprint, request, jsonify, g # IMPORT g

def create_item_bp(db_service, item_service, token_required):
    bp = Blueprint('item_routes', __name__)

    @bp.route('/stats', methods=['GET'])
    def get_stats():
        stats = db_service.items.find_stats()
        return jsonify(stats), 200

    @bp.route('', methods=['GET'])
    @token_required
    def get_items():
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('per_page', 20))
        search_query = request.args.get('search', '')
        item_type = request.args.get('type', '')
        user_id_filter = request.args.get('user_id', '')
        
        # FINAL FIX: Access user ID via g.user_id 
        authenticated_user_id = g.user_id 

        query = {}
        if item_type in ['lost', 'found']:
            query['type'] = item_type
        
        if user_id_filter:
            if user_id_filter == 'me':
                if authenticated_user_id:
                    query['user_id'] = authenticated_user_id
                else:
                    # If 'user_id=me' is requested without a valid token, FAIL (401)
                    return jsonify({"message": "Authentication required to view your items."}), 401
            else:
                query['user_id'] = user_id_filter
        
        items = item_service.find_all_items(
            query=query, 
            limit=limit, 
            offset=(page - 1) * limit
        )
        
        total_items = db_service.items.collection.count_documents(query)

        return jsonify({
            "items": items,
            "pagination": {
                "page": page,
                "per_page": limit,
                "total": total_items,
                "has_next": (page * limit) < total_items
            }
        }), 200

    @bp.route('/<item_id>', methods=['GET'])
    def get_item(item_id):
        item = db_service.items.find_item_by_id(item_id)
        if not item:
            return jsonify({"message": "Item not found"}), 404

        is_owner = False
        return jsonify({"item": item, "is_owner": is_owner}), 200

    @bp.route('', methods=['POST'])
    @token_required
    def create_item():
        user_id = g.user_id 
        if not user_id:
            return jsonify({'message': 'Authentication required.'}), 401
            
        from ai_models.tasks import process_new_item 

        image_files = request.files.getlist('images')
        form_data = request.form.to_dict()

        new_item_id = item_service.create_item(user_id, form_data, image_files)

        process_new_item.delay(new_item_id)
        
        return jsonify({"id": new_item_id, "message": "Item created successfully"}), 201

    @bp.route('/<item_id>', methods=['PUT'])
    @token_required
    def update_item_status(item_id):
        user_id = g.user_id
        if not user_id:
            return jsonify({'message': 'Authentication required.'}), 401

        item = db_service.items.find_item_by_id(item_id)
        if not item or item['user_id'] != user_id:
            return jsonify({"message": "Item not found or access denied"}), 403
            
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status == 'resolved':
            if db_service.items.update_item(item_id, {'status': 'resolved'}):
                return jsonify({"message": "Item status updated to resolved"}), 200
            
        return jsonify({"message": "Invalid status update or failed to update"}), 400

    @bp.route('/<item_id>', methods=['DELETE']) 
    @token_required
    def delete_item(item_id):
        user_id = g.user_id
        if not user_id:
            return jsonify({'message': 'Authentication required.'}), 401

        item = db_service.items.find_item_by_id(item_id)
        if not item or item['user_id'] != user_id:
            return jsonify({"message": "Item not found or access denied"}), 403

        if db_service.items.delete_item(item_id):
            return jsonify({"message": "Item deleted successfully"}), 200
        return jsonify({"message": "Failed to delete item"}), 500
    
    return bp