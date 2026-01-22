# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError

class TestExecutionDeclaration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestExecutionDeclaration, cls).setUpClass()
        # Create Project & Approved Planning
        cls.project = cls.env['project.project'].create({
            'name': 'Execution Project',
            'is_execution_project': True,
        })
        cls.planning = cls.env['execution.planning'].create({
            'name': 'Approved Planning',
            'project_id': cls.project.id,
        })
        cls.lot = cls.env['execution.planning.lot'].create({
            'name': 'Lot A',
            'planning_id': cls.planning.id,
        })
        cls.task = cls.env['execution.planning.task'].create({
            'name': 'Task A',
            'lot_id': cls.lot.id,
            'weight': 100.0,
        })
        cls.planning.action_submit()
        cls.planning.action_approve()

    def test_01_progress_declaration_constraints(self):
        """Test progress declaration constraints: 0-100% and progressive only"""
        # Test 0-100 range
        with self.assertRaises(ValidationError):
            self.env['execution.progress'].create({
                'task_id': self.task.id,
                'declared_percentage': 105.0,
                'comment': 'Over 100%',
            })
            
        # Test progressive only (requires a validated declaration first)
        decl1 = self.env['execution.progress'].create({
            'task_id': self.task.id,
            'declared_percentage': 30.0,
            'comment': '30% done',
        })
        # Mocking validation (directly calling action_validate since we are testing executionpm_execution)
        decl1.write({'state': 'under_review'})
        decl1.action_validate()
        
        # Now try to declare less than 30%
        with self.assertRaises(ValidationError):
            self.env['execution.progress'].create({
                'task_id': self.task.id,
                'declared_percentage': 25.0,
                'comment': 'Going backwards',
            })

    def test_02_mandatory_attachments(self):
        """Test that attachments are mandatory on submission"""
        decl = self.env['execution.progress'].create({
            'task_id': self.task.id,
            'declared_percentage': 50.0,
            'comment': 'No attachments',
        })
        
        with self.assertRaises(UserError):
            decl.action_submit()
            
        # Add attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'proof.jpg',
            'datas': b'empty',
            'res_model': 'execution.progress',
            'res_id': decl.id,
        })
        decl.write({'attachment_ids': [(4, attachment.id)]})
        
        # Should now submit successfully
        decl.action_submit()
        self.assertEqual(decl.state, 'submitted')

    def test_03_edit_lock(self):
        """Test that validated records cannot be modified"""
        decl = self.env['execution.progress'].create({
            'task_id': self.task.id,
            'declared_percentage': 100.0,
            'comment': 'Finish',
        })
        # Add attachment to allow submission
        attachment = self.env['ir.attachment'].create({
            'name': 'proof.jpg',
            'datas': b'empty',
        })
        decl.write({'attachment_ids': [(4, attachment.id)]})
        
        decl.action_submit()
        decl.action_start_review()
        decl.action_validate()
        
        # Try to change comment
        with self.assertRaises(UserError):
            decl.write({'comment': 'Sneaky edit'})
