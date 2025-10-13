@api_bp.route('/elections/<int:election_id>', methods=['DELETE'])
def delete_election(election_id):
    try:
        election = Election.query.get_or_404(election_id)
        db.session.delete(election)
        db.session.commit()
        return jsonify({'message': 'Election deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
